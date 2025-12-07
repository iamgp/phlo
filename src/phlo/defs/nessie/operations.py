# operations.py - Dagster operations for Nessie branch management and versioning
# Provides reusable ops for Git-like operations on the Iceberg catalog
# enabling data versioning workflows and branch management

"""
Dagster operations for Nessie branch management.

Provides ops for creating, merging, listing, and tagging branches.
"""

from __future__ import annotations

import dagster as dg
import requests

from phlo.defs.nessie import NessieResource


# --- Nessie Operations ---
# Dagster ops for branch management operations
@dg.op(
    name="list_branches",
    description="List all branches and tags in Nessie catalog",
    tags={"nessie": "branching"},
)
def list_branches(context, nessie: NessieResource) -> dg.MaterializeResult:
    """
    List all branches and tags in the Nessie catalog.

    Returns metadata about available branches for observability.
    """
    try:
        branches = nessie.get_branches()

        # Separate branches and tags
        branches_list = [ref for ref in branches if ref.get("type") == "BRANCH"]
        tags_list = [ref for ref in branches if ref.get("type") == "TAG"]

        branch_names = [b["name"] for b in branches_list]
        tag_names = [t["name"] for t in tags_list]

        context.log.info(f"Found {len(branches_list)} branches: {branch_names}")
        context.log.info(f"Found {len(tags_list)} tags: {tag_names}")

        return dg.MaterializeResult(
            metadata={
                "branches_count": dg.MetadataValue.int(len(branches_list)),
                "tags_count": dg.MetadataValue.int(len(tags_list)),
                "branches": dg.MetadataValue.json(branch_names),
                "tags": dg.MetadataValue.json(tag_names),
                "all_refs": dg.MetadataValue.json([ref["name"] for ref in branches]),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to list branches: {e}")
        raise


@dg.op(
    name="create_branch",
    description="Create a new branch from source reference",
    tags={"nessie": "branching"},
)
def create_branch(
    context, nessie: NessieResource, branch_name: str, source_ref: str = "main"
) -> dg.MaterializeResult:
    """
    Create a new branch from a source reference.

    Args:
        branch_name: Name of the new branch
        source_ref: Source branch/tag to branch from (default: main)
    """
    try:
        context.log.info(f"Creating branch '{branch_name}' from '{source_ref}'")

        result = nessie.create_branch(branch_name, source_ref)

        context.log.info(f"Successfully created branch '{branch_name}'")
        context.log.info(f"Branch hash: {result.get('hash', 'unknown')}")

        return dg.MaterializeResult(
            metadata={
                "branch_name": dg.MetadataValue.text(branch_name),
                "source_ref": dg.MetadataValue.text(source_ref),
                "branch_hash": dg.MetadataValue.text(result.get("hash", "unknown")),
                "operation": dg.MetadataValue.text("create_branch"),
            }
        )

    except requests.HTTPError as e:
        if e.response.status_code == 409:
            context.log.warning(f"Branch '{branch_name}' already exists")
            return dg.MaterializeResult(
                metadata={
                    "branch_name": dg.MetadataValue.text(branch_name),
                    "status": dg.MetadataValue.text("already_exists"),
                    "operation": dg.MetadataValue.text("create_branch"),
                }
            )
        else:
            context.log.error(f"Failed to create branch: {e}")
            raise
    except Exception as e:
        context.log.error(f"Failed to create branch: {e}")
        raise


@dg.op(
    name="merge_branch",
    description="Merge source branch into target branch",
    tags={"nessie": "branching"},
)
def merge_branch(
    context, nessie: NessieResource, source_branch: str, target_branch: str
) -> dg.MaterializeResult:
    """
    Merge source branch into target branch.

    This is the key operation for promoting changes from dev to main.

    Args:
        source_branch: Branch to merge from (e.g., "dev")
        target_branch: Branch to merge into (e.g., "main")
    """
    try:
        context.log.info(f"Merging '{source_branch}' into '{target_branch}'")

        result = nessie.merge_branch(source_branch, target_branch)

        context.log.info(
            f"Successfully merged '{source_branch}' into '{target_branch}'"
        )

        return dg.MaterializeResult(
            metadata={
                "source_branch": dg.MetadataValue.text(source_branch),
                "target_branch": dg.MetadataValue.text(target_branch),
                "result": dg.MetadataValue.json(result),
                "operation": dg.MetadataValue.text("merge_branch"),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to merge branches: {e}")
        raise


@dg.op(
    name="tag_snapshot",
    description="Create a tag for the current snapshot",
    tags={"nessie": "branching"},
)
def tag_snapshot(
    context, nessie: NessieResource, tag_name: str, source_ref: str = "main"
) -> dg.MaterializeResult:
    """
    Create a tag for the current snapshot of a reference.

    Useful for marking production releases or important milestones.

    Args:
        tag_name: Name of the tag to create
        source_ref: Reference to tag (default: main)
    """
    try:
        context.log.info(f"Creating tag '{tag_name}' for '{source_ref}'")

        result = nessie.tag_snapshot(tag_name, source_ref)

        context.log.info(f"Successfully created tag '{tag_name}'")

        return dg.MaterializeResult(
            metadata={
                "tag_name": dg.MetadataValue.text(tag_name),
                "source_ref": dg.MetadataValue.text(source_ref),
                "tag_hash": dg.MetadataValue.text(result.get("hash", "unknown")),
                "operation": dg.MetadataValue.text("tag_snapshot"),
            }
        )

    except Exception as e:
        context.log.error(f"Failed to create tag: {e}")
        raise


# --- Aggregation Function ---
# Builds operation job definitions
def build_defs() -> dg.Definitions:
    """Build Nessie operations definitions."""
    return dg.Definitions(
        jobs=[
            # Create jobs for each operation
            dg.define_asset_job(
                name="list_branches_job",
                selection=[],
                description="List all branches and tags",
            ),
            dg.define_asset_job(
                name="create_branch_job",
                selection=[],
                description="Create a new branch",
            ),
            dg.define_asset_job(
                name="merge_branch_job",
                selection=[],
                description="Merge branches",
            ),
            dg.define_asset_job(
                name="tag_snapshot_job",
                selection=[],
                description="Create a snapshot tag",
            ),
        ],
    )
