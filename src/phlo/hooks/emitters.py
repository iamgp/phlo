"""Helper emitters for publishing hook events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from phlo.hooks.bus import HookBus, get_hook_bus
from phlo.hooks.events import (
    IngestionEvent,
    LineageEvent,
    PublishEvent,
    QualityResultEvent,
    ServiceLifecycleEvent,
    TelemetryEvent,
    TransformEvent,
)


@dataclass(frozen=True)
class IngestionEventContext:
    """Shared context for ingestion event emissions."""

    asset_key: str
    table_name: str
    group_name: str
    partition_key: str | None = None
    run_id: str | None = None
    branch_name: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


class IngestionEventEmitter:
    """Emit ingestion lifecycle events with a shared context."""

    def __init__(self, context: IngestionEventContext, hook_bus: HookBus | None = None) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_start(self, *, status: str = "started") -> None:
        """Emit an ingestion start event."""

        self._emit(event_type="ingestion.start", status=status, metrics=None, error=None)

    def emit_end(
        self,
        *,
        status: str,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Emit an ingestion end event."""

        self._emit(event_type="ingestion.end", status=status, metrics=metrics, error=error)

    def _emit(
        self,
        *,
        event_type: str,
        status: str | None,
        metrics: dict[str, Any] | None,
        error: str | None,
    ) -> None:
        self._hook_bus.emit(
            IngestionEvent(
                event_type=event_type,
                asset_key=self._context.asset_key,
                table_name=self._context.table_name,
                group_name=self._context.group_name,
                partition_key=self._context.partition_key,
                run_id=self._context.run_id,
                branch_name=self._context.branch_name,
                status=status,
                metrics=metrics or {},
                error=error,
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class TransformEventContext:
    """Shared context for transform event emissions."""

    tool: str
    project_dir: str | None = None
    target: str | None = None
    partition_key: str | None = None
    asset_key: str | None = None
    model_names: list[str] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)


class TransformEventEmitter:
    """Emit transform lifecycle events with a shared context."""

    def __init__(self, context: TransformEventContext, hook_bus: HookBus | None = None) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_start(self, *, status: str = "started") -> None:
        """Emit a transform start event."""

        self._emit(event_type="transform.start", status=status, metrics=None, error=None)

    def emit_end(
        self,
        *,
        status: str,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Emit a transform end event."""

        self._emit(event_type="transform.end", status=status, metrics=metrics, error=error)

    def _emit(
        self,
        *,
        event_type: str,
        status: str | None,
        metrics: dict[str, Any] | None,
        error: str | None,
    ) -> None:
        self._hook_bus.emit(
            TransformEvent(
                event_type=event_type,
                tool=self._context.tool,
                project_dir=self._context.project_dir,
                target=self._context.target,
                partition_key=self._context.partition_key,
                asset_key=self._context.asset_key,
                model_names=list(self._context.model_names),
                status=status,
                metrics=metrics or {},
                error=error,
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class PublishEventContext:
    """Shared context for publish event emissions."""

    asset_key: str | None = None
    target_system: str | None = None
    tables: dict[str, str] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)


class PublishEventEmitter:
    """Emit publish lifecycle events with a shared context."""

    def __init__(self, context: PublishEventContext, hook_bus: HookBus | None = None) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_start(self, *, status: str = "started") -> None:
        """Emit a publish start event."""

        self._emit(event_type="publish.start", status=status, metrics=None, error=None)

    def emit_end(
        self,
        *,
        status: str,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Emit a publish end event."""

        self._emit(event_type="publish.end", status=status, metrics=metrics, error=error)

    def _emit(
        self,
        *,
        event_type: str,
        status: str | None,
        metrics: dict[str, Any] | None,
        error: str | None,
    ) -> None:
        self._hook_bus.emit(
            PublishEvent(
                event_type=event_type,
                asset_key=self._context.asset_key,
                target_system=self._context.target_system,
                tables=self._context.tables.copy(),
                status=status,
                metrics=metrics or {},
                error=error,
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class QualityResultEventContext:
    """Shared context for quality result event emissions."""

    asset_key: str
    partition_key: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


class QualityResultEventEmitter:
    """Emit quality result events with a shared context."""

    def __init__(
        self,
        context: QualityResultEventContext,
        hook_bus: HookBus | None = None,
    ) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_result(
        self,
        *,
        check_name: str,
        passed: bool,
        severity: str | None = None,
        check_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a quality result event."""

        self._hook_bus.emit(
            QualityResultEvent(
                event_type="quality.result",
                asset_key=self._context.asset_key,
                check_name=check_name,
                passed=passed,
                severity=severity,
                check_type=check_type,
                partition_key=self._context.partition_key,
                metadata=metadata or {},
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class LineageEventContext:
    """Shared context for lineage event emissions."""

    tags: dict[str, str] = field(default_factory=dict)


class LineageEventEmitter:
    """Emit lineage events with a shared context."""

    def __init__(self, context: LineageEventContext, hook_bus: HookBus | None = None) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_edges(
        self,
        *,
        edges: list[tuple[str, str]],
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a lineage edges event."""

        self._hook_bus.emit(
            LineageEvent(
                event_type="lineage.edges",
                edges=list(edges),
                asset_keys=list(asset_keys) if asset_keys else [],
                metadata=metadata or {},
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class TelemetryEventContext:
    """Shared context for telemetry event emissions."""

    tags: dict[str, str] = field(default_factory=dict)


class TelemetryEventEmitter:
    """Emit telemetry events with a shared context."""

    def __init__(self, context: TelemetryEventContext, hook_bus: HookBus | None = None) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit_metric(
        self,
        *,
        name: str,
        value: Any | None = None,
        unit: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Emit a telemetry metric event."""

        self._emit(
            event_type="telemetry.metric",
            name=name,
            value=value,
            level=None,
            unit=unit,
            payload=payload,
        )

    def emit_log(
        self,
        *,
        name: str,
        level: str,
        value: Any | None = None,
        unit: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Emit a telemetry log event."""

        self._emit(
            event_type="telemetry.log",
            name=name,
            value=value,
            level=level,
            unit=unit,
            payload=payload,
        )

    def _emit(
        self,
        *,
        event_type: str,
        name: str,
        value: Any | None,
        level: str | None,
        unit: str | None,
        payload: dict[str, Any] | None,
    ) -> None:
        self._hook_bus.emit(
            TelemetryEvent(
                event_type=event_type,
                name=name,
                value=value,
                level=level,
                unit=unit,
                payload=payload or {},
                tags=self._context.tags.copy(),
            )
        )


@dataclass(frozen=True)
class ServiceLifecycleEventContext:
    """Shared context for service lifecycle event emissions."""

    service_name: str
    project_name: str | None = None
    project_root: str | None = None
    container_name: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


class ServiceLifecycleEventEmitter:
    """Emit service lifecycle events with a shared context."""

    def __init__(
        self, context: ServiceLifecycleEventContext, hook_bus: HookBus | None = None
    ) -> None:
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()

    def emit(
        self,
        *,
        phase: str,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a service lifecycle event for the given phase."""

        tags = self._context.tags.copy()
        tags["service"] = self._context.service_name
        tags["phase"] = phase
        self._hook_bus.emit(
            ServiceLifecycleEvent(
                event_type=f"service.{phase}",
                service_name=self._context.service_name,
                project_name=self._context.project_name,
                project_root=self._context.project_root,
                container_name=self._context.container_name,
                phase=phase,
                status=status,
                metadata=metadata or {},
                tags=tags,
            )
        )
