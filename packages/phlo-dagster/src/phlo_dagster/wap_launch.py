"""Pre-launch Write-Audit-Publish coordination for Dagster runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phlo.capabilities.interfaces import VersionedCatalog
from phlo.capabilities.resolver import resolve_capability
from phlo.exceptions import PhloConfigError

WAP_BRANCH_TAG = "phlo/wap_branch"
WAP_REF_TAG = "phlo/ref"
WAP_RUN_ID_TAG = "phlo/run_id"
WAP_BRANCH_PREFIX = "pipeline-run-"


@dataclass(frozen=True)
class WapLaunch:
    """The logical identity and branch prepared before a Dagster run starts."""

    logical_run_id: str
    branch: str
    catalog: VersionedCatalog
    created_branch: bool

    @property
    def tags(self) -> dict[str, str]:
        """Return the Dagster tags that bind stages to this WAP branch."""
        return {
            WAP_RUN_ID_TAG: self.logical_run_id,
            WAP_BRANCH_TAG: self.branch,
            WAP_REF_TAG: self.branch,
        }

    def cleanup_if_created(self) -> None:
        """Remove only the branch created by this launch attempt."""
        if self.created_branch:
            self.catalog.delete_branch(self.branch)


def prepare_wap_launch(*, logical_run_id: str) -> WapLaunch:
    """Ensure a WAP branch and tags exist before asking Dagster to start work."""
    resolution = resolve_capability("catalog")
    if resolution is None or not (
        resolution.support.supports_refs and resolution.support.supports_promote
    ):
        raise PhloConfigError(
            message="WAP materialization requires a catalog with refs and promotion support.",
            suggestions=["Configure a versioned catalog such as phlo-nessie before using --wap."],
        )

    catalog: Any = resolution.provider
    if not isinstance(catalog, VersionedCatalog):
        raise PhloConfigError(
            message="Configured catalog does not implement the WAP branch lifecycle.",
            suggestions=["Configure a VersionedCatalog-compatible provider before using --wap."],
        )

    branch = f"{WAP_BRANCH_PREFIX}{logical_run_id}"
    if catalog.get_branch_hash(branch):
        return WapLaunch(
            logical_run_id=logical_run_id,
            branch=branch,
            catalog=catalog,
            created_branch=False,
        )

    if catalog.create_branch(branch, from_ref="main") is None:
        raise PhloConfigError(
            message=f"Could not create WAP branch {branch!r} from main.",
            suggestions=["Confirm the configured catalog can create branches from main."],
        )

    return WapLaunch(
        logical_run_id=logical_run_id,
        branch=branch,
        catalog=catalog,
        created_branch=True,
    )
