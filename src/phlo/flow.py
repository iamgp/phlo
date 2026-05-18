"""Terse flow authoring decorators for publish, observe, and backfill assets."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from phlo._flow_authoring import append_asset, asset_key, build_run, contract_metadata
from phlo.capabilities import AssetCheckSpec, AssetSpec
from phlo.contracts import SLA, Consumer

_PUBLISH_ASSETS: list[AssetSpec] = []
_OBSERVE_ASSETS: list[AssetSpec] = []
_BACKFILL_ASSETS: list[AssetSpec] = []


def publish(
    *,
    table: str,
    audience: list[str] | None = None,
    owner: str | None = None,
    freshness_hours: int | None = None,
    depends_on: list[str] | None = None,
    group: str = "publish",
    consumers: list[Consumer | str] | None = None,
    sla: SLA | None = None,
    description: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Mark a curated table as a publishable data-product surface."""

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        append_asset(
            _PUBLISH_ASSETS,
            AssetSpec(
                key=asset_key("publish", table),
                group=group,
                description=description or fn.__doc__,
                kinds={"publish", "data_product"},
                tags={"provider": "core", "asset_type": "publish"},
                metadata={
                    "table": table,
                    "audience": list(audience or []),
                    "freshness_hours": freshness_hours,
                    **contract_metadata(owner=owner, consumers=consumers, sla=sla),
                },
                deps=list(depends_on or []),
                run=build_run(fn),
            ),
        )
        return fn

    return _decorator


def observe(
    *,
    table: str,
    freshness_hours: int | None = None,
    row_count_change: dict[str, float] | None = None,
    depends_on: list[str] | None = None,
    group: str = "observe",
    description: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register operational health checks for a table or asset."""

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        key = asset_key("observe", table)
        checks: list[AssetCheckSpec] = []
        if freshness_hours is not None:
            checks.append(
                AssetCheckSpec(
                    name="freshness_hours",
                    asset_key=key,
                    fn=None,
                    blocking=False,
                    description=f"Warn when {table} is older than {freshness_hours} hours.",
                    severity="warning",
                    tags={"check_type": "freshness"},
                )
            )
        if row_count_change is not None:
            checks.append(
                AssetCheckSpec(
                    name="row_count_change",
                    asset_key=key,
                    fn=None,
                    blocking=False,
                    description=f"Watch row-count movement for {table}.",
                    severity="warning",
                    tags={"check_type": "volume"},
                )
            )

        append_asset(
            _OBSERVE_ASSETS,
            AssetSpec(
                key=key,
                group=group,
                description=description or fn.__doc__,
                kinds={"observe", "operational_check"},
                tags={"provider": "core", "asset_type": "observe"},
                metadata={
                    "table": table,
                    "freshness_hours": freshness_hours,
                    "row_count_change": dict(row_count_change or {}),
                },
                deps=list(depends_on or []),
                run=build_run(fn),
                checks=checks,
            ),
        )
        return fn

    return _decorator


def backfill(
    *,
    target: str,
    partitions: dict[str, Any],
    mode: str = "replace-partitions",
    depends_on: list[str] | None = None,
    group: str = "backfill",
    owner: str | None = None,
    description: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a repeatable backfill job."""

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        append_asset(
            _BACKFILL_ASSETS,
            AssetSpec(
                key=asset_key("backfill", target),
                group=group,
                description=description or fn.__doc__,
                kinds={"backfill"},
                tags={"provider": "core", "asset_type": "backfill", "mode": mode},
                metadata={
                    "target": target,
                    "partitions": dict(partitions),
                    "mode": mode,
                    "owner": owner,
                },
                deps=list(depends_on or []),
                run=build_run(fn),
            ),
        )
        return fn

    return _decorator


def get_publish_assets() -> list[AssetSpec]:
    """Return registered publish asset specs."""
    return list(_PUBLISH_ASSETS)


def clear_publish_assets() -> None:
    """Clear registered publish asset specs."""
    _PUBLISH_ASSETS.clear()


def get_observe_assets() -> list[AssetSpec]:
    """Return registered observe asset specs."""
    return list(_OBSERVE_ASSETS)


def clear_observe_assets() -> None:
    """Clear registered observe asset specs."""
    _OBSERVE_ASSETS.clear()


def get_backfill_assets() -> list[AssetSpec]:
    """Return registered backfill asset specs."""
    return list(_BACKFILL_ASSETS)


def clear_backfill_assets() -> None:
    """Clear registered backfill asset specs."""
    _BACKFILL_ASSETS.clear()


__all__ = [
    "backfill",
    "clear_backfill_assets",
    "clear_observe_assets",
    "clear_publish_assets",
    "get_backfill_assets",
    "get_observe_assets",
    "get_publish_assets",
    "observe",
    "publish",
]
