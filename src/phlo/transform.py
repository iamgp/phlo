"""Provider-neutral transformation authoring decorators."""

from __future__ import annotations

from collections.abc import Callable

from phlo._flow_authoring import append_asset, asset_key, build_run, contract_metadata
from phlo.capabilities import AssetSpec
from phlo.contracts import SLA, Consumer

_TRANSFORM_ASSETS: list[AssetSpec] = []


def sql(
    *,
    table: str,
    depends_on: list[str] | None = None,
    materialized: str = "table",
    group: str = "transform",
    owner: str | None = None,
    consumers: list[Consumer | str] | None = None,
    sla: SLA | None = None,
    description: str | None = None,
) -> Callable[[Callable[..., str]], Callable[..., str]]:
    """Register a SQL transform asset."""

    def _decorator(fn: Callable[..., str]) -> Callable[..., str]:
        sql_text = fn()
        append_asset(
            _TRANSFORM_ASSETS,
            AssetSpec(
                key=asset_key("transform", table),
                group=group,
                description=description or fn.__doc__,
                kinds={"sql", "transform"},
                tags={
                    "provider": "core",
                    "asset_type": "transform",
                    "transform_type": "sql",
                    "materialized": materialized,
                },
                metadata={
                    "table": table,
                    "sql": sql_text,
                    "materialized": materialized,
                    **contract_metadata(owner=owner, consumers=consumers, sla=sla),
                },
                deps=list(depends_on or []),
                run=build_run(fn),
            ),
        )
        return fn

    return _decorator


def get_transform_assets() -> list[AssetSpec]:
    """Return registered transform asset specs."""
    return list(_TRANSFORM_ASSETS)


def clear_transform_assets() -> None:
    """Clear registered transform asset specs."""
    _TRANSFORM_ASSETS.clear()


__all__ = ["clear_transform_assets", "get_transform_assets", "sql"]
