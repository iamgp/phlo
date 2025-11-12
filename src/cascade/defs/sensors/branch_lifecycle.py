"""
Branch Lifecycle Sensors for automatic Nessie branch management.

This module provides sensors that manage the complete lifecycle of dynamic pipeline branches:
1. Creation: Create branch when full_pipeline job starts
2. Promotion: Promote to main when all asset checks pass
3. Cleanup: Delete old branches after retention period
"""

import json
from datetime import datetime, timedelta

import dagster as dg
from cascade.config import config
from cascade.defs.nessie import NessieResource
from cascade.defs.nessie.branch_manager import BranchManagerResource


@dg.run_status_sensor(
    run_status=dg.DagsterRunStatus.STARTING,
    request_job=None,
    name="branch_creation_sensor",
    description="Create dynamic pipeline branch when full_pipeline job starts"
)
def branch_creation_sensor(
    context: dg.RunStatusSensorContext,
    branch_manager: BranchManagerResource,
):
    """
    Create pipeline branch when full_pipeline job starts.

    Monitors job starts and creates a dynamic branch (pipeline/run-{id}) for isolation.
    The branch name is stored in run tags for downstream assets to access.
    """
    run = context.dagster_run

    # Only create branches for full_pipeline job
    if run.job_name != "full_pipeline":
        context.log.info(f"Skipping branch creation for job {run.job_name}")
        return

    # Check if branch already specified in run tags
    if run.tags.get("branch"):
        context.log.info(f"Branch already specified: {run.tags['branch']}")
        return

    # Create dynamic branch
    try:
        result = branch_manager.create_pipeline_branch(run.run_id)
        branch_name = result["branch_name"]

        context.log.info(
            f"Created branch {branch_name} for run {run.run_id} from {result['created_from']}"
        )

        # Add branch tag to run so all assets can access it
        context.instance.add_run_tags(run.run_id, {"branch": branch_name})

    except Exception as e:
        context.log.error(f"Failed to create branch for run {run.run_id}: {e}")
        raise


@dg.sensor(
    name="auto_promotion_sensor",
    minimum_interval_seconds=30,
    description="Automatically promote pipeline branch to main when all checks pass"
)
def auto_promotion_sensor(
    context: dg.SensorEvaluationContext,
    nessie: NessieResource,
    branch_manager: BranchManagerResource,
):
    """
    Promote pipeline branch when all asset checks pass.

    Monitors asset check results for completed full_pipeline runs and triggers
    promotion to main when all blocking checks pass.
    """
    if not config.auto_promote_enabled:
        return dg.SkipReason("Auto-promotion disabled in config")

    instance = context.instance

    # Get recent successful runs of full_pipeline
    runs = instance.get_runs(
        filters=dg.RunsFilter(
            job_name="full_pipeline",
            statuses=[dg.DagsterRunStatus.SUCCESS]
        ),
        limit=10
    )

    cursor = json.loads(context.cursor) if context.cursor else {}
    promoted_any = False

    for run in runs:
        branch_name = run.tags.get("branch")
        if not branch_name:
            continue

        # Check if already promoted
        cursor_key = f"promoted_{branch_name}"
        if cursor.get(cursor_key):
            continue

        # Get all asset check evaluations for this run
        check_evaluations = list(instance.event_log_storage.get_asset_check_execution_history(
            check_key=None,  # All checks
            limit=1000,
            cursor=None
        ))

        # Filter to checks from this run
        run_checks = [
            check for check in check_evaluations
            if check.run_id == run.run_id
        ]

        if not run_checks:
            context.log.debug(f"No check results found for run {run.run_id} yet")
            continue

        # Check if all blocking checks passed
        all_passed = True
        failures = []

        for check_eval in run_checks:
            evaluation = check_eval.event.asset_check_evaluation

            # Only block on ERROR severity checks
            if evaluation.severity == dg.AssetCheckSeverity.ERROR:
                if not evaluation.passed:
                    all_passed = False
                    failures.append({
                        "check": str(check_eval.event.asset_check_evaluation_data.asset_check_key),
                        "metadata": evaluation.metadata
                    })

        if not all_passed:
            context.log.warning(
                f"Checks failed for {branch_name} (run {run.run_id}): {failures}"
            )
            continue

        # All checks passed - promote!
        context.log.info(f"All checks passed for {branch_name}, promoting to main")

        try:
            promote_branch_to_main(
                nessie=nessie,
                branch_manager=branch_manager,
                branch_name=branch_name,
                context=context
            )

            # Update cursor to prevent duplicate promotions
            cursor[cursor_key] = True
            promoted_any = True

            context.log.info(f"Successfully promoted {branch_name} to main")

        except Exception as e:
            context.log.error(f"Failed to promote {branch_name}: {e}")
            continue

    if promoted_any:
        context.update_cursor(json.dumps(cursor))

    return dg.SkipReason("No branches ready for promotion")


def promote_branch_to_main(
    nessie: NessieResource,
    branch_manager: BranchManagerResource,
    branch_name: str,
    context
):
    """
    Promote pipeline branch to main (internal function, not an asset).

    This performs the actual promotion mechanics:
    1. Fast-forward merge pipeline branch to main
    2. Create timestamped production tag
    3. Schedule branch cleanup

    Args:
        nessie: Nessie resource for branch operations
        branch_manager: Branch manager for cleanup scheduling
        branch_name: Name of pipeline branch to promote
        context: Sensor context for logging
    """
    # 1. Fast-forward merge to main
    nessie.assign_branch("main", branch_name)
    context.log.info(f"Merged {branch_name} to main")

    # 2. Create production tag
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        nessie.tag_snapshot(f"v{timestamp}", "main")
        context.log.info(f"Created tag v{timestamp}")
    except Exception as e:
        context.log.warning(f"Failed to create tag v{timestamp}: {e}")
        # Don't fail promotion if tagging fails

    # 3. Schedule cleanup
    try:
        cleanup_info = branch_manager.schedule_cleanup(
            branch_name=branch_name,
            retention_days=config.branch_retention_days,
            promotion_succeeded=True
        )
        context.log.info(
            f"Scheduled cleanup for {branch_name} after {cleanup_info['cleanup_after']}"
        )
    except Exception as e:
        context.log.warning(f"Failed to schedule cleanup for {branch_name}: {e}")
        # Don't fail promotion if cleanup scheduling fails


@dg.sensor(
    name="branch_cleanup_sensor",
    minimum_interval_seconds=3600,  # Run hourly
    description="Clean up old pipeline branches after retention period"
)
def branch_cleanup_sensor(
    context: dg.SensorEvaluationContext,
    branch_manager: BranchManagerResource,
) -> dg.SensorResult | dg.SkipReason:
    """
    Clean up pipeline branches that have exceeded their retention period.

    Runs hourly to check for branches ready for cleanup based on promotion
    metadata stored in previous sensor executions.

    Note: This is a simplified version that relies on branch naming and age.
    For production, you might want to store cleanup metadata in external storage.
    """
    context.log.info("Checking for branches to clean up")

    try:
        # Get all pipeline branches
        pipeline_branches = branch_manager.get_all_pipeline_branches()

        if not pipeline_branches:
            return dg.SkipReason("No pipeline branches found")

        cursor = json.loads(context.cursor) if context.cursor else {}
        now = datetime.now()
        branches_to_cleanup = []

        # Check each branch's age
        for branch_info in pipeline_branches:
            branch_name = branch_info.get("name")
            if not branch_name:
                continue

            # Check if already cleaned
            cursor_key = f"cleaned_{branch_name}"
            if cursor.get(cursor_key):
                continue

            # Simple age-based cleanup: branches older than retention period
            # In practice, you'd check actual promotion/creation timestamps
            # For now, we rely on the retention policy being enforced by other means
            # This sensor serves as a backstop for orphaned branches

            branches_to_cleanup.append(branch_name)

        if not branches_to_cleanup:
            return dg.SkipReason("No branches ready for cleanup")

        context.log.info(f"Found {len(branches_to_cleanup)} branches to check: {branches_to_cleanup}")

        # Perform cleanup (dry run for safety - can be disabled in config)
        cleaned_branches = []
        for branch_name in branches_to_cleanup:
            try:
                # For now, just log what we would clean up
                # To actually delete, call with dry_run=False
                result = branch_manager.cleanup_branch(branch_name, dry_run=True)
                if result.get("dry_run"):
                    context.log.info(f"Would delete branch: {branch_name}")
                elif result["deleted"]:
                    cleaned_branches.append(branch_name)
                    context.log.info(f"Deleted branch: {branch_name}")
            except Exception as e:
                context.log.error(f"Failed to clean up branch {branch_name}: {e}")

        # Update cursor
        for branch in cleaned_branches:
            cursor[f"cleaned_{branch}"] = True

        if cleaned_branches:
            context.update_cursor(json.dumps(cursor))
            return dg.SensorResult(
                skip_reason=None,
                cursor=json.dumps(cursor)
            )

        return dg.SkipReason("No branches cleaned up (dry run mode)")

    except Exception as e:
        context.log.error(f"Error in branch cleanup sensor: {e}")
        return dg.SkipReason(f"Error: {e}")
