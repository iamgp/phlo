"""Helper emitters for publishing hook events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from phlo.hooks.bus import HookBus, get_hook_bus
from phlo.hooks.events import IngestionEvent


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
