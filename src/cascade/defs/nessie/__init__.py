"""
Nessie branch management operations for Git-like data versioning.

This module provides Dagster assets and operations for managing Nessie branches,
enabling Git-like workflows for data engineering pipelines.
"""

from __future__ import annotations

import json
from typing import Any

import dagster as dg
import requests

from cascade.config import config


class NessieResource(dg.ConfigurableResource):
    """
    Dagster resource for interacting with Nessie REST API v2.

    Provides convenient methods for branch management operations.
    Uses Nessie API v2 for forward compatibility.
    """

    def get_branches(self) -> list[dict[str, Any]]:
        """Get all branches and tags."""
        response = requests.get(f"{config.nessie_api_v1_uri}/trees")
        response.raise_for_status()
        return response.json().get("references", [])

    def create_branch(self, branch_name: str, source_ref: str = "main") -> dict[str, Any]:
        """Create a new branch from source reference."""
        source_hash = self._get_ref_hash(source_ref)
        data = {"type": "BRANCH", "name": branch_name, "hash": source_hash}
        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/tree",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def merge_branch(self, source_branch: str, target_branch: str) -> dict[str, Any]:
        """Merge source branch into target branch."""
        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/branch/{target_branch}/merge",
            json={"fromRefName": source_branch},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def delete_branch(self, branch_name: str) -> None:
        """Delete a branch."""
        response = requests.delete(f"{config.nessie_api_v1_uri}/trees/branch/{branch_name}")
        response.raise_for_status()

    def tag_snapshot(self, tag_name: str, source_ref: str = "main") -> dict[str, Any]:
        """Create a tag for the current snapshot of a reference."""
        source_hash = self._get_ref_hash(source_ref)
        data = {"type": "TAG", "name": tag_name, "hash": source_hash}
        response = requests.post(
            f"{config.nessie_api_v1_uri}/trees/tree",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def _get_ref_hash(self, ref: str) -> str:
        """Get the hash of a reference."""
        response = requests.get(f"{config.nessie_api_v1_uri}/trees/tree/{ref}")
        response.raise_for_status()
        return response.json()["hash"]


def build_defs() -> dg.Definitions:
    """Build Nessie branch management definitions."""
    from cascade.defs.nessie.workflow import build_defs as build_workflow_defs

    return dg.Definitions.merge(
        dg.Definitions(
            resources={
                "nessie": NessieResource(),
            }
        ),
        build_workflow_defs(),
    )
