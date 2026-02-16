"""Nessie resources for branch management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests

from phlo_nessie.settings import get_settings


@dataclass
class BranchInfo:
    """Branch metadata returned by Nessie.

    Attributes:
        name: Branch name.
        hash: Current branch hash, if available.
        created_at: Branch creation timestamp, if provided by Nessie.
    """

    name: str
    hash: str | None
    created_at: datetime | None


class NessieResource:
    """Lightweight Nessie REST client."""

    def __init__(self, base_url: str | None = None):
        """Initialize a Nessie client.

        Args:
            base_url: Optional explicit Nessie base URL.
        """

        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            settings = get_settings()
            self.base_url = f"http://{settings.nessie_host}:{settings.nessie_port}"

    def _url(self, path: str) -> str:
        """Build a full Nessie URL.

        Args:
            path: Nessie API path.

        Returns:
            Fully qualified API URL.
        """

        return f"{self.base_url}{path}"

    def list_branches(self) -> list[BranchInfo]:
        """List all branch references from Nessie.

        Returns:
            Parsed branch information for each branch reference.
        """

        response = requests.get(self._url("/api/v1/trees"), timeout=10)
        response.raise_for_status()
        payload = response.json() or {}
        branches: list[BranchInfo] = []
        for ref in payload.get("references", []):
            if ref.get("type") != "BRANCH":
                continue
            created_at = None
            metadata = ref.get("metadata") or {}
            if isinstance(metadata, dict):
                created_raw = metadata.get("createdAt") or metadata.get("created_at")
                if isinstance(created_raw, str):
                    try:
                        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                    except ValueError:
                        created_at = None
            branches.append(
                BranchInfo(name=ref.get("name", ""), hash=ref.get("hash"), created_at=created_at)
            )
        return branches

    def get_branch_hash(self, name: str) -> str | None:
        """Fetch the current hash for a branch.

        Args:
            name: Branch name.

        Returns:
            Branch hash when found, otherwise ``None``.
        """

        response = requests.get(self._url(f"/api/v1/trees/tree/{name}"), timeout=10)
        if response.status_code >= 400:
            return None
        data = response.json() or {}
        return data.get("hash")

    def delete_branch(self, name: str) -> bool:
        """Delete a branch by name.

        Args:
            name: Branch name.

        Returns:
            ``True`` if deletion succeeded, else ``False``.
        """

        branch_hash = self.get_branch_hash(name)
        if not branch_hash:
            return False
        response = requests.delete(
            self._url(f"/api/v1/trees/tree/{name}"),
            params={"expectedHash": branch_hash},
            timeout=10,
        )
        return response.status_code < 300


class BranchManagerResource:
    """Convenience wrapper for cleaning up Nessie branches."""

    def __init__(self, nessie: NessieResource | None = None):
        """Initialize a branch manager.

        Args:
            nessie: Optional Nessie client instance.
        """

        self._nessie = nessie or NessieResource()

    def get_all_pipeline_branches(self) -> list[BranchInfo]:
        """Return non-system branches used for pipelines.

        Returns:
            Branches excluding ``main`` and ``dev``.
        """

        branches = self._nessie.list_branches()
        return [branch for branch in branches if branch.name not in {"main", "dev"}]

    def cleanup_branch(self, name: str) -> bool:
        """Delete a pipeline branch.

        Args:
            name: Branch name.

        Returns:
            ``True`` when cleanup succeeds, else ``False``.
        """

        return self._nessie.delete_branch(name)
