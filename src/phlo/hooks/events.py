"""Hook event payload definitions for the capability plugin system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

EVENT_VERSION = "1.0"


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


@dataclass(kw_only=True)
class HookEvent:
    """Base event payload shared by all hook events."""

    event_type: str
    version: str = EVENT_VERSION
    timestamp: datetime = field(default_factory=_utc_now)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(kw_only=True)
class ServiceLifecycleEvent(HookEvent):
    """Lifecycle event emitted around service start/stop phases."""

    service_name: str
    project_name: str | None = None
    project_root: str | None = None
    container_name: str | None = None
    phase: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class IngestionEvent(HookEvent):
    """Event emitted for ingestion lifecycle stages."""

    asset_key: str
    table_name: str
    group_name: str
    partition_key: str | None = None
    run_id: str | None = None
    branch_name: str | None = None
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class TransformEvent(HookEvent):
    """Event emitted for transformation lifecycle stages."""

    tool: str
    project_dir: str | None = None
    target: str | None = None
    partition_key: str | None = None
    asset_key: str | None = None
    model_names: list[str] = field(default_factory=list)
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class PublishEvent(HookEvent):
    """Event emitted when publishing data to downstream targets."""

    asset_key: str | None = None
    target_system: str | None = None
    tables: dict[str, str] = field(default_factory=dict)
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class QualityResultEvent(HookEvent):
    """Event emitted with quality check outcomes."""

    asset_key: str
    check_name: str
    passed: bool
    severity: str | None = None
    check_type: str | None = None
    partition_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class LineageEvent(HookEvent):
    """Event emitted for lineage edges between assets."""

    edges: list[tuple[str, str]] = field(default_factory=list)
    asset_keys: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class TelemetryEvent(HookEvent):
    """Event emitted for telemetry metrics and logs."""

    name: str
    value: Any | None = None
    level: str | None = None
    unit: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
