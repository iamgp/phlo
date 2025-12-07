# __init__.py - Nessie resource and branch management for Git-like data versioning
# Provides the NessieResource class and aggregates workflow definitions
# for managing Iceberg catalog branches and tags

"""
Nessie branch management operations for Git-like data versioning.

This module provides Dagster assets and operations for managing Nessie branches,
enabling Git-like workflows for data engineering pipelines.
"""

from __future__ import annotations

from typing import Any

import dagster as dg
import requests

from phlo.config import config


# --- Nessie Resource ---
# Dagster resource for Nessie REST API interactions
class NessieResource(dg.ConfigurableResource):
    """
    Dagster resource for interacting with Nessie REST API v2.

    Provides convenient methods for branch management operations.
    Uses Nessie API v2 for forward compatibility.
    """

    def get_branches(self) -> list[dict[str, Any]]:
        """Get all branches and tags."""
        response = requests.get(f"{config.nessie_api_v1_uri}/trees", timeout=30)
        response.raise_for_status()
        return response.json().get("references", [])

    def create_branch(self, branch_name: str, source_ref: str = "main") -> dict[str, Any]:
        """Create a new branch from source reference."""
        source_hash = self._get_ref_hash(source_ref)
        data = {"type": "BRANCH", "name": branch_name, "hash": source_hash}
        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/tree",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def merge_branch(self, source_branch: str, target_branch: str) -> dict[str, Any]:
        """Merge source branch into target branch."""
        source_hash = self._get_ref_hash(source_branch)
        target_hash = self._get_ref_hash(target_branch)

        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/branch/{target_branch}/merge",
            params={"expectedHash": target_hash},
            json={"fromRefName": source_branch, "fromHash": source_hash},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def assign_branch(self, target_branch: str, source_branch: str) -> dict[str, Any]:
        """
        Assign target branch to point to the same commit as source branch.

        This is a fast-forward operation that makes target_branch point to the
        exact same commit as source_branch, essentially "promoting" the source
        to target without merging. This avoids merge conflicts.
        """
        source_hash = self._get_ref_hash(source_branch)
        target_hash = self._get_ref_hash(target_branch)

        response = requests.put(
            f"{config.nessie_api_v1_uri}/trees/branch/{target_branch}",
            params={"expectedHash": target_hash},
            json={"type": "BRANCH", "name": target_branch, "hash": source_hash},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        return {
            "status": "success",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "new_hash": source_hash,
        }

    def delete_branch(self, branch_name: str) -> None:
        """Delete a branch."""
        branch_hash = self._get_ref_hash(branch_name)
        response = requests.delete(
            f"{config.nessie_api_v1_uri}/trees/branch/{branch_name}",
            params={"expectedHash": branch_hash},
            timeout=30,
        )
        response.raise_for_status()

    def tag_snapshot(self, tag_name: str, source_ref: str = "main") -> dict[str, Any]:
        """Create a tag for the current snapshot of a reference."""
        source_hash = self._get_ref_hash(source_ref)
        data = {"type": "TAG", "name": tag_name, "hash": source_hash}
        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/tree",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _get_ref_hash(self, ref: str) -> str:
        """Get the hash of a reference."""
        response = requests.get(
            f"{config.nessie_api_v1_uri}/trees/tree/{ref}",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["hash"]


# --- Aggregation Function ---
# Builds complete Nessie definitions with resource and workflow assets
def build_defs() -> dg.Definitions:
    """Build Nessie branch management definitions."""
    from phlo.defs.nessie.branch_manager import BranchManagerResource
    from phlo.defs.nessie.workflow import build_defs as build_workflow_defs

    return dg.Definitions.merge(
        dg.Definitions(
            resources={
                "nessie": NessieResource(),
                "branch_manager": BranchManagerResource(
                    nessie=NessieResource(),
                    retention_days=config.branch_retention_days,
                    retention_days_failed=config.branch_retention_days_failed,
                ),
            }
        ),
        build_workflow_defs(),
    )
