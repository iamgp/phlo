"""Capability specs for orchestrator-agnostic assets and checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Iterable

from phlo.capabilities.runtime import RuntimeContext


@dataclass(frozen=True, slots=True)
class PartitionSpec:
    """Partitioning metadata for an asset."""

    kind: str
    start_date: date | None = None
    timezone: str | None = None


@dataclass(frozen=True, slots=True)
class RunSpec:
    """Execution details for an asset."""

    fn: Callable[[RuntimeContext], Iterable["RunResult"]]
    max_runtime_seconds: int | None = None
    max_retries: int | None = None
    retry_delay_seconds: int | None = None
    cron: str | None = None
    freshness_hours: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class AssetCheckSpec:
    """Check spec for assets, with optional execution function."""

    name: str
    asset_key: str
    fn: Callable[[RuntimeContext], "CheckResult"] | None = None
    blocking: bool = True
    description: str | None = None
    severity: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AssetSpec:
    """Orchestrator-agnostic asset specification."""

    key: str
    group: str | None
    description: str | None
    kinds: set[str] = field(default_factory=set)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    partitions: PartitionSpec | None = None
    deps: list[str] = field(default_factory=list)
    resources: set[str] = field(default_factory=set)
    run: RunSpec | None = None
    checks: list[AssetCheckSpec] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ResourceSpec:
    """Resource definitions to register with the orchestrator adapter."""

    name: str
    resource: Any


@dataclass(frozen=True, slots=True)
class MaterializeResult:
    """Result for a successful or skipped materialization."""

    metadata: dict[str, Any] = field(default_factory=dict)
    status: str | None = None


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result for a quality or contract check."""

    check_name: str
    asset_key: str
    passed: bool
    severity: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


RunResult = MaterializeResult | CheckResult
