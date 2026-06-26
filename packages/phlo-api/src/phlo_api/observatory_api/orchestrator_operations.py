"""Capability-backed orchestrator operation resolution for Observatory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException

from phlo.capabilities import (
    OrchestratorOperationsSpec,
    list_capabilities,
    register_capability,
    resolve_capability,
)
from phlo.capabilities.discovery import discover_capabilities


class LegacyDagsterOrchestratorOperationsProvider:
    """Adapter for the built-in Dagster Observatory operation implementation."""

    async def get_run_status(self, run_id: str) -> Any:
        from phlo_api.observatory_api.dagster import get_run_status

        return await get_run_status(run_id)

    async def retry_run(self, run_id: str, request: Mapping[str, Any]) -> Any:
        from phlo_api.observatory_api.dagster import RetryRunRequest, retry_run

        return await retry_run(run_id, RetryRunRequest(**dict(request)))

    async def cancel_run(self, run_id: str, request: Mapping[str, Any]) -> Any:
        from phlo_api.observatory_api.dagster import CancelRunRequest, cancel_run

        return await cancel_run(run_id, CancelRunRequest(**dict(request)))

    async def get_materialization_history(self, asset_key_path: str, *, limit: int = 10) -> Any:
        from phlo_api.observatory_api.dagster import get_materialization_history

        return await get_materialization_history(asset_key_path, limit=limit)

    async def materialize_asset(self, asset_key_path: str, request: Mapping[str, Any]) -> Any:
        from phlo_api.observatory_api.dagster import MaterializeAssetRequest, materialize_asset

        return await materialize_asset(asset_key_path, MaterializeAssetRequest(**dict(request)))

    async def backfill_asset(self, asset_key_path: str, request: Mapping[str, Any]) -> Any:
        from phlo_api.observatory_api.dagster import BackfillAssetRequest, backfill_asset

        return await backfill_asset(asset_key_path, BackfillAssetRequest(**dict(request)))

    async def list_partitions(self, asset_key_path: str) -> Any:
        from phlo_api.observatory_api.dagster import list_partitions

        return await list_partitions(asset_key_path)


def resolve_orchestrator_operations(provider_name: str | None = None) -> Any:
    """Resolve the active orchestrator operations provider."""
    ensure_orchestrator_operations_registered()
    resolved = resolve_capability("orchestrator_operations", provider_name)
    if resolved is not None:
        return resolved.provider

    available = list_capabilities("orchestrator_operations")
    detail: dict[str, Any] = {
        "error": "orchestrator_operations_unavailable",
        "available_providers": available,
    }
    if provider_name:
        detail["requested_provider"] = provider_name
    elif len(available) > 1:
        detail["error"] = "orchestrator_operations_ambiguous"
        detail["message"] = (
            "Multiple orchestrator operation providers are installed. Configure a default "
            "or pass an explicit provider."
        )
    else:
        detail["message"] = "Install or enable an orchestrator operations provider."
    raise HTTPException(status_code=422, detail=detail)


def ensure_orchestrator_operations_registered() -> None:
    """Discover provider capabilities and install the legacy Dagster fallback."""
    discover_capabilities()
    if list_capabilities("orchestrator_operations"):
        return
    register_capability(
        "orchestrator_operations",
        OrchestratorOperationsSpec(
            name="dagster",
            provider=LegacyDagsterOrchestratorOperationsProvider(),
            metadata={"package": "phlo-api", "legacy": True},
        ),
    )
