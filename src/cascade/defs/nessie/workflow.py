# workflow.py - Nessie branching workflow assets for Git-like data versioning
# Defines Dagster assets that manage dynamic pipeline branches and production promotion
# using Nessie branches for isolated data development and controlled promotion

"""
Nessie branching workflows for data engineering.

Provides assets that orchestrate dynamic branch workflows:
- Pipeline branch creation (pipeline/run-{id})
- Validation-gated promotion (pipeline -> main)
- Production tagging
"""

from __future__ import annotations

from datetime import datetime

import dagster as dg
from cascade.config import config
from cascade.defs.nessie import NessieResource
from cascade.defs.nessie.branch_manager import BranchManagerResource


# Production promotion asset (updated for dynamic branches)
@dg.asset(
    name="promote_to_main",
    group_name="nessie",
    description="Promote pipeline branch to main after validation",
    compute_kind="nessie",
    deps=[dg.AssetKey(["validation_orchestrator"])],
)
def promote_to_main(
    context: dg.AssetExecutionContext,
    nessie: NessieResource,
    branch_manager: BranchManagerResource,
) -> dg.MaterializeResult:
    """
    Promote pipeline branch to main after validation.

    This is the key asset for production deployment:
    1. Verifies all validations passed
    2. Fast-forward merges pipeline branch into main
    3. Creates timestamped production tag
    4. Schedules branch cleanup

    Run config:
        branch_name: Name of pipeline branch to promote (e.g., "pipeline/run-a1b2c3d4")

    Returns:
        MaterializeResult with promotion metadata for cleanup sensor
    """
    branch_name = context.run_config.get("branch_name")

    if not branch_name:
        raise ValueError("branch_name must be provided in run_config")

    context.log.info(f"Promoting branch {branch_name} to main")

    # 1. Verify validation_orchestrator passed (redundant check for safety)
    instance = context.instance
    validation_events = instance.get_event_records(
        event_records_filter=dg.EventRecordsFilter(
            event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=dg.AssetKey(["validation_orchestrator"])
        ),
        limit=1
    )

    if validation_events:
        validation_metadata = validation_events[0].asset_materialization.metadata
        all_passed = validation_metadata.get("all_passed")
        if not all_passed:
            raise Exception(
                f"Cannot promote: validation failures exist. "
                f"Failures: {validation_metadata.get('blocking_failures')}"
            )

    # 2. Fast-forward merge to main
    try:
        nessie.assign_branch("main", branch_name)
        context.log.info(f"Successfully merged {branch_name} to main")
    except Exception as e:
        context.log.error(f"Failed to merge {branch_name} to main: {e}")
        raise

    # 3. Create production tag
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        tag_result = nessie.tag_snapshot(f"v{timestamp}", "main")
        context.log.info(f"Created tag: {tag_result['name']}")
    except Exception as e:
        context.log.error(f"Failed to create tag: {e}")
        raise

    # 4. Schedule branch cleanup
    cleanup_result = branch_manager.schedule_cleanup(
        branch_name=branch_name,
        retention_days=config.branch_retention_days,
        promotion_succeeded=True
    )

    context.log.info(
        f"Scheduled cleanup for {branch_name} after {cleanup_result['cleanup_after']}"
    )

    return dg.MaterializeResult(
        metadata={
            "branch_promoted": branch_name,
            "promoted_at": timestamp,
            "tag_created": tag_result["name"],
            "cleanup_scheduled_for": cleanup_result["cleanup_after"]
        }
    )


# Branch status reporting asset
@dg.asset(
    name="nessie_branch_status",
    group_name="nessie",
    description="Report current branch status and health",
    compute_kind="nessie",
)
def nessie_branch_status(context, nessie: NessieResource) -> dg.MaterializeResult:
    """
    Report the current status of branches and tags.

    Provides observability into the current state of the Nessie catalog.
    """
    try:
        branches = nessie.get_branches()

        branches_list = [ref for ref in branches if ref.get("type") == "BRANCH"]
        tags_list = [ref for ref in branches if ref.get("type") == "TAG"]

        # Check for required branches
        branch_names = [b["name"] for b in branches_list]
        has_main = "main" in branch_names
        has_dev = "dev" in branch_names

        # Get commit info for main branch
        main_info = None
        if has_main:
            try:
                main_ref = next(b for b in branches_list if b["name"] == "main")
                main_info = {
                    "hash": main_ref.get("hash", "unknown"),
                    "commit_time": main_ref.get("commit", {}).get("commitTime", "unknown")
                }
            except:
                pass

        health_status = "healthy" if has_main else "unhealthy"

        return dg.MaterializeResult(
            metadata={
                "health_status": dg.MetadataValue.text(health_status),
                "branches_count": dg.MetadataValue.int(len(branches_list)),
                "tags_count": dg.MetadataValue.int(len(tags_list)),
                "has_main_branch": dg.MetadataValue.bool(has_main),
                "has_dev_branch": dg.MetadataValue.bool(has_dev),
                "main_branch_info": dg.MetadataValue.json(main_info or {}),
                "all_branches": dg.MetadataValue.json(branch_names),
                "all_tags": dg.MetadataValue.json([t["name"] for t in tags_list]),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to get branch status: {e}")
        return dg.MaterializeResult(
            metadata={
                "health_status": dg.MetadataValue.text("error"),
                "error": dg.MetadataValue.text(str(e)),
            }
        )


# --- Aggregation Function ---
# Builds workflow asset definitions
def build_defs() -> dg.Definitions:
    """Build Nessie workflow definitions."""
    return dg.Definitions(
        assets=[
            nessie_dev_branch,
            promote_dev_to_main,
            nessie_branch_status,
        ],
    )
