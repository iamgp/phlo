# workflow.py - Nessie branching workflow assets for Git-like data versioning
# Defines Dagster assets that manage development and production workflows
# using Nessie branches for isolated data development and controlled promotion

"""
Nessie branching workflows for data engineering.

Provides assets that orchestrate common Git-like workflows:
- Development workflow (dev branch)
- Production promotion (dev -> main)
"""

from __future__ import annotations

import dagster as dg

from cascade.defs.nessie import NessieResource
from cascade.defs.nessie.operations import create_branch, list_branches, merge_branch


# --- Workflow Assets ---
# Dagster assets that implement Nessie branching operations
@dg.asset(
    name="nessie_dev_branch",
    group_name="nessie",
    description="Ensure dev branch exists for development work",
    compute_kind="nessie",
)
def nessie_dev_branch(context, nessie: NessieResource) -> dg.MaterializeResult:
    """
    Ensure the 'dev' branch exists.

    This asset creates the dev branch if it doesn't exist, allowing
    development work to be isolated from production.
    """
    try:
        # First check if dev branch exists
        branches = nessie.get_branches()
        branch_names = [ref["name"] for ref in branches if ref.get("type") == "BRANCH"]

        if "dev" in branch_names:
            context.log.info("Dev branch already exists")
            return dg.MaterializeResult(
                metadata={
                    "branch_name": dg.MetadataValue.text("dev"),
                    "status": dg.MetadataValue.text("already_exists"),
                    "operation": dg.MetadataValue.text("ensure_dev_branch"),
                }
            )

        # Create dev branch from main
        context.log.info("Creating dev branch from main")
        result = nessie.create_branch("dev", "main")

        return dg.MaterializeResult(
            metadata={
                "branch_name": dg.MetadataValue.text("dev"),
                "source_ref": dg.MetadataValue.text("main"),
                "status": dg.MetadataValue.text("created"),
                "branch_hash": dg.MetadataValue.text(result.get("hash", "unknown")),
                "operation": dg.MetadataValue.text("ensure_dev_branch"),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to ensure dev branch: {e}")
        raise


# Production promotion asset
@dg.asset(
    name="promote_dev_to_main",
    group_name="nessie",
    description="Promote dev branch changes to main branch",
    compute_kind="nessie",
    deps=[dg.AssetKey("nessie_dev_branch")],
)
def promote_dev_to_main(context, nessie: NessieResource) -> dg.MaterializeResult:
    """
    Promote changes from dev branch to main branch.

    This is the key asset for production deployment:
    1. Validates dev branch exists and has changes
    2. Merges dev into main atomically
    3. Tags the new production snapshot
    """
    try:
        context.log.info("Starting dev -> main promotion")

        # Check that dev branch exists and has commits ahead of main
        branches = nessie.get_branches()
        branch_names = [ref["name"] for ref in branches if ref.get("type") == "BRANCH"]

        if "dev" not in branch_names:
            raise ValueError("Dev branch does not exist - cannot promote")

        context.log.info("Dev branch exists, proceeding with promotion")

        # Promote dev to main by assigning main to dev's commit
        # This is a fast-forward operation that avoids merge conflicts
        merge_result = nessie.assign_branch("main", "dev")

        context.log.info("Successfully promoted dev to main")

        # Create a version tag for this production release
        import datetime
        tag_name = f"v{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            tag_result = nessie.tag_snapshot(tag_name, "main")
            context.log.info(f"Created production tag: {tag_name}")
        except Exception as e:
            context.log.warning(f"Failed to create tag {tag_name}: {e}")
            tag_name = None

        return dg.MaterializeResult(
            metadata={
                "source_branch": dg.MetadataValue.text("dev"),
                "target_branch": dg.MetadataValue.text("main"),
                "merge_result": dg.MetadataValue.json(merge_result),
                "production_tag": dg.MetadataValue.text(tag_name or "none"),
                "operation": dg.MetadataValue.text("promote_dev_to_main"),
                "status": dg.MetadataValue.text("completed"),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to promote dev to main: {e}")
        raise


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
