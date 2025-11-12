"""
Promotion and Cleanup Sensors for automatic branch management.

This module provides sensors that:
1. Auto-promote validated branches to main
2. Clean up old pipeline branches after retention period
"""

import json
from datetime import datetime

import dagster as dg
from cascade.config import config
from cascade.defs.nessie.branch_manager import BranchManagerResource


@dg.sensor(
    name="auto_promotion_sensor",
    minimum_interval_seconds=30,
    description="Automatically promotes pipeline branch to main after validation passes"
)
def auto_promotion_sensor(
    context: dg.SensorEvaluationContext,
) -> dg.SensorResult | dg.SkipReason:
    """
    Monitors validation_orchestrator completion.
    Triggers promote_to_main if all validations passed.

    Returns:
        RunRequest to materialize promote_to_main with branch context
        or SkipReason if conditions not met
    """
    if not config.auto_promote_enabled:
        return dg.SkipReason("Auto-promotion disabled in config")

    # Query latest validation_orchestrator materialization
    instance = context.instance

    events = instance.get_event_records(
        event_records_filter=dg.EventRecordsFilter(
            event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=dg.AssetKey(["validation_orchestrator"])
        ),
        limit=1
    )

    if not events:
        return dg.SkipReason("No validation_orchestrator runs found")

    latest_event = events[0]
    metadata = latest_event.asset_materialization.metadata

    all_passed = metadata.get("all_passed", False)
    branch_name = metadata.get("branch_name")

    if not all_passed:
        blocking_failures = metadata.get("blocking_failures", [])
        context.log.warning(
            f"Validation failed for branch {branch_name}. Failures: {blocking_failures}"
        )
        return dg.SkipReason(f"Validation failed for branch {branch_name}")

    # Check if we've already promoted this branch
    cursor_key = f"promoted_{branch_name}"
    if context.cursor and context.cursor.get(cursor_key):
        return dg.SkipReason(f"Branch {branch_name} already promoted")

    context.log.info(f"All validations passed for branch {branch_name}. Triggering promotion.")

    # Update cursor to prevent duplicate promotions
    new_cursor = context.cursor.copy() if context.cursor else {}
    new_cursor[cursor_key] = True
    context.update_cursor(json.dumps(new_cursor))

    return dg.RunRequest(
        run_key=f"promote_{branch_name}_{latest_event.timestamp}",
        run_config={"ops": {"promote_to_main": {"config": {"branch_name": branch_name}}}},
        tags={"branch": branch_name, "auto_promoted": "true"}
    )


@dg.sensor(
    name="branch_cleanup_sensor",
    minimum_interval_seconds=3600,  # Run hourly
    description="Cleans up old pipeline branches after retention period"
)
def branch_cleanup_sensor(
    context: dg.SensorEvaluationContext,
    branch_manager: BranchManagerResource,
) -> dg.SensorResult | dg.SkipReason:
    """
    Cleans up pipeline branches that have exceeded their retention period.

    Triggered hourly to check for branches ready for cleanup.
    """
    context.log.info("Checking for branches to clean up")

    # Query Dagster storage for branches scheduled for cleanup
    instance = context.instance

    promote_events = instance.get_event_records(
        event_records_filter=dg.EventRecordsFilter(
            event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=dg.AssetKey(["promote_to_main"])
        ),
        limit=100
    )

    branches_to_cleanup = []
    now = datetime.now()

    for event in promote_events:
        metadata = event.asset_materialization.metadata
        branch_name = metadata.get("branch_promoted")
        cleanup_after_str = metadata.get("cleanup_scheduled_for")

        if not cleanup_after_str:
            continue

        cleanup_after = datetime.fromisoformat(cleanup_after_str)

        # Check if it's time to cleanup
        if now >= cleanup_after:
            cursor_key = f"cleaned_{branch_name}"
            cursor = json.loads(context.cursor) if context.cursor else {}
            if not cursor.get(cursor_key):
                branches_to_cleanup.append(branch_name)

    if not branches_to_cleanup:
        return dg.SkipReason("No branches ready for cleanup")

    context.log.info(f"Cleaning up {len(branches_to_cleanup)} branches: {branches_to_cleanup}")

    # Perform cleanup
    cleaned_branches = []
    for branch_name in branches_to_cleanup:
        try:
            result = branch_manager.cleanup_branch(branch_name, dry_run=False)
            if result["deleted"]:
                cleaned_branches.append(branch_name)
                context.log.info(f"Deleted branch: {branch_name}")
        except Exception as e:
            context.log.error(f"Failed to delete branch {branch_name}: {e}")

    # Update cursor
    cursor = json.loads(context.cursor) if context.cursor else {}
    for branch in cleaned_branches:
        cursor[f"cleaned_{branch}"] = True
    context.update_cursor(json.dumps(cursor))

    return dg.SensorResult(
        skip_reason=None,
        cursor=json.dumps(cursor)
    )
