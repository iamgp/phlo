"""Provider-neutral Observatory run read model."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from phlo_api.observatory_api.observatory_models import (
    RunStatus,
    ObservatoryResourceRef,
    ObservatoryRun,
)

_DAGSTER_STATUS_MAP: dict[str, RunStatus] = {
    "SUCCESS": "succeeded",
    "FAILURE": "failed",
    "STARTED": "running",
    "QUEUED": "queued",
    "CANCELED": "cancelled",
}


def load_runs() -> list[ObservatoryRun]:
    """Load provider-neutral orchestrator runs."""
    try:
        legacy_runs = asyncio.run(_load_legacy_dagster_runs())
    except Exception:
        return []

    return [_normalize_legacy_dagster_run(run) for run in legacy_runs]


async def _load_legacy_dagster_runs() -> list[dict[str, Any]]:
    from phlo_api.observatory_api.dagster import get_runs

    runs = await get_runs()
    return runs if isinstance(runs, list) else []


def _normalize_legacy_dagster_run(run: Mapping[str, Any]) -> ObservatoryRun:
    started_at = _optional_str(run.get("startTime"))
    completed_at = _optional_str(run.get("endTime"))

    return ObservatoryRun(
        id=_first_str(run, ("id", "runId"), "unknown"),
        name=_first_str(run, ("jobName", "pipelineName"), "run"),
        status=_normalize_status(run.get("status")),
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=_duration_seconds(started_at, completed_at),
        assets=_normalize_asset_refs(run.get("assetKeys")),
        metadata={"source": "dagster"},
    )


def _first_str(run: Mapping[str, Any], keys: tuple[str, ...], default: str) -> str:
    for key in keys:
        value = run.get(key)
        if value:
            return str(value)
    return default


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC).isoformat()
    return str(value)


def _normalize_status(status: Any) -> RunStatus:
    if status is None:
        return "unknown"
    return _DAGSTER_STATUS_MAP.get(str(status).upper(), "unknown")


def _normalize_asset_refs(asset_keys: Any) -> list[ObservatoryResourceRef]:
    if not isinstance(asset_keys, Sequence) or isinstance(asset_keys, (str, bytes)):
        return []

    refs: list[ObservatoryResourceRef] = []
    for asset_key in asset_keys:
        if not isinstance(asset_key, Sequence) or isinstance(asset_key, (str, bytes)):
            continue
        asset_id = ".".join(str(part) for part in asset_key if part is not None)
        if asset_id:
            refs.append(ObservatoryResourceRef(kind="asset", id=asset_id, label=asset_id))
    return refs


def _duration_seconds(started_at: str | None, completed_at: str | None) -> float | None:
    if not started_at or not completed_at:
        return None

    try:
        started = _parse_timestamp(started_at)
        completed = _parse_timestamp(completed_at)
    except ValueError:
        return None

    return (completed - started).total_seconds()


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromtimestamp(float(value), UTC)
    except ValueError:
        pass
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
