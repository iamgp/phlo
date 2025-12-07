"""
Branch Manager Resource for dynamic Nessie branch lifecycle management.

This module provides a Dagster resource for creating, tracking, and cleaning up
dynamic pipeline branches in Nessie. It supports the dynamic branch workflow where
each pipeline run gets its own isolated branch for development and testing.
"""

from datetime import datetime, timedelta
from typing import Any

import dagster as dg

from phlo.defs.nessie import NessieResource


class BranchManagerResource(dg.ConfigurableResource):
    """Manages dynamic Nessie branch lifecycle for pipeline isolation."""

    nessie: NessieResource
    retention_days: int
    retention_days_failed: int

    def create_pipeline_branch(
        self, run_id: str, source_ref: str = "main"
    ) -> dict[str, Any]:
        """
        Create a new pipeline branch for this pipeline run.

        Pipeline branches are named: pipeline/run-{run_id}

        Args:
            run_id: Dagster run ID (shortened to first 8 chars for readability)
            source_ref: Source branch to branch from (default: main)

        Returns:
            {
                "branch_name": "pipeline/run-{run_id}",
                "created_from": source_ref,
                "created_at": ISO timestamp,
                "source_hash": commit hash
            }

        Example:
            >>> branch_manager.create_pipeline_branch("a1b2c3d4-e5f6")
            {
                "branch_name": "pipeline/run-a1b2c3d4",
                "created_from": "main",
                "created_at": "2025-01-11T14:30:00",
                "source_hash": "abc123def456"
            }
        """
        # Use first 8 chars of run_id for readability
        short_run_id = run_id[:8] if len(run_id) > 8 else run_id
        branch_name = f"pipeline/run-{short_run_id}"

        # Create branch from source
        result = self.nessie.create_branch(branch_name, source_ref)

        return {
            "branch_name": branch_name,
            "created_from": source_ref,
            "created_at": datetime.now().isoformat(),
            "source_hash": result.get("hash", "unknown"),
        }

    def schedule_cleanup(
        self, branch_name: str, retention_days: int, promotion_succeeded: bool
    ) -> dict[str, Any]:
        """
        Schedule branch for cleanup after retention period.

        This method returns metadata that should be stored in the promote_to_main
        asset's MaterializeResult. The cleanup sensor will read this metadata
        and delete branches after the retention period expires.

        Args:
            branch_name: Branch to cleanup (e.g., "pipeline/run-a1b2c3d4")
            retention_days: Days to retain the branch
            promotion_succeeded: Whether promotion to main succeeded

        Returns:
            {
                "branch_name": branch_name,
                "cleanup_after": ISO timestamp,
                "promotion_succeeded": bool,
                "scheduled_at": ISO timestamp
            }

        Example:
            >>> branch_manager.schedule_cleanup("pipeline/run-a1b2c3d4", 7, True)
            {
                "branch_name": "pipeline/run-a1b2c3d4",
                "cleanup_after": "2025-01-18T14:30:00",
                "promotion_succeeded": True,
                "scheduled_at": "2025-01-11T14:30:00"
            }
        """
        cleanup_after = datetime.now() + timedelta(days=retention_days)

        return {
            "branch_name": branch_name,
            "cleanup_after": cleanup_after.isoformat(),
            "promotion_succeeded": promotion_succeeded,
            "scheduled_at": datetime.now().isoformat(),
            "retention_days": retention_days,
        }

    def cleanup_branch(self, branch_name: str, dry_run: bool = False) -> dict[str, Any]:
        """
        Clean up a specific pipeline branch.

        Args:
            branch_name: Branch to delete
            dry_run: If True, don't actually delete, just return what would be deleted

        Returns:
            {
                "branch_name": branch_name,
                "deleted": bool,
                "deleted_at": ISO timestamp or None if dry_run
            }

        Example:
            >>> branch_manager.cleanup_branch("pipeline/run-a1b2c3d4")
            {
                "branch_name": "pipeline/run-a1b2c3d4",
                "deleted": True,
                "deleted_at": "2025-01-18T14:30:00"
            }
        """
        if dry_run:
            return {
                "branch_name": branch_name,
                "deleted": False,
                "deleted_at": None,
                "dry_run": True,
            }

        try:
            self.nessie.delete_branch(branch_name)
            return {
                "branch_name": branch_name,
                "deleted": True,
                "deleted_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "branch_name": branch_name,
                "deleted": False,
                "error": str(e),
                "deleted_at": None,
            }

    def get_all_pipeline_branches(self) -> list[dict[str, Any]]:
        """
        Get all pipeline branches (branches matching 'pipeline/' prefix).

        Returns:
            List of branch metadata dicts:
            [
                {
                    "name": "pipeline/run-a1b2c3d4",
                    "hash": "abc123",
                    "metadata": {...}
                }
            ]

        Example:
            >>> branch_manager.get_all_pipeline_branches()
            [
                {"name": "pipeline/run-a1b2c3d4", "hash": "abc123", ...},
                {"name": "pipeline/run-e5f6g7h8", "hash": "def456", ...}
            ]
        """
        all_branches = self.nessie.get_branches()

        # Filter for pipeline branches only
        pipeline_branches = [
            branch
            for branch in all_branches
            if branch.get("name", "").startswith("pipeline/")
        ]

        return pipeline_branches
