"""Hook event system for Phlo plugins.

The hook system provides an event-driven architecture for plugin communication.
Plugins can emit events during various lifecycle stages (ingestion, transformation,
quality checks, etc.) and other plugins can register handlers to react to these
events.

This module uses lazy loading to prevent circular imports during plugin discovery.
All exports are resolved on first access via ``__getattr__`` to avoid loading
submodules at import time.

Key Components:
    - :class:`~phlo.hooks.bus.HookBus`: Central event dispatcher
    - :class:`~phlo.hooks.events.HookEvent`: Base event payload
    - :class:`~phlo.hooks.emitters.IngestionEventEmitter`: Ingestion lifecycle events
    - :class:`~phlo.hooks.emitters.TransformEventEmitter`: Transform lifecycle events
    - :class:`~phlo.hooks.emitters.QualityResultEventEmitter`: Quality check events

Event Types:
    The system supports multiple event types for different lifecycle stages:
    - ``ingestion.start``, ``ingestion.end``: Ingestion operations
    - ``transform.start``, ``transform.end``: dbt transformations
    - ``quality.result``: Data quality check results
    - ``service.start``, ``service.stop``: Service lifecycle
    - ``schema_migration.applied``, ``data_migration.completed``: Migrations

Example:
    ```python
    from phlo.hooks import get_hook_bus, IngestionEventEmitter, IngestionEventContext

    # Get the global hook bus
    bus = get_hook_bus()

    # Create an emitter for ingestion events
    context = IngestionEventContext(
        asset_key="my_table",
        table_name="my_table",
        group_name="ingestion"
    )
    emitter = IngestionEventEmitter(context)

    # Emit events during your operation
    emitter.emit_start()
    # ... perform ingestion ...
    emitter.emit_end(status="success")
    ```

Note:
    This module intentionally avoids importing submodules at import time to prevent
    cycles during plugin discovery. Exports are resolved lazily via ``__getattr__``.

"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

__all__ = [
    "EVENT_VERSION",
    "HookBus",
    "HookCorrelation",
    "HookEvent",
    "IngestionEventContext",
    "IngestionEventEmitter",
    "DataMigrationEventContext",
    "DataMigrationEventEmitter",
    "LineageEventContext",
    "LineageEventEmitter",
    "PublishEventContext",
    "PublishEventEmitter",
    "QualityResultEventContext",
    "QualityResultEventEmitter",
    "SchemaMigrationEventContext",
    "SchemaMigrationEventEmitter",
    "ServiceLifecycleEventContext",
    "ServiceLifecycleEventEmitter",
    "TelemetryEventContext",
    "TelemetryEventEmitter",
    "TransformEventContext",
    "TransformEventEmitter",
    "IngestionEvent",
    "DataMigrationEvent",
    "LineageEvent",
    "PublishEvent",
    "QualityResultEvent",
    "SchemaMigrationEvent",
    "ServiceLifecycleEvent",
    "TelemetryEvent",
    "TransformEvent",
    "LogEvent",
    "get_hook_bus",
]

_BUS_EXPORTS = {"HookBus", "get_hook_bus"}
_EMITTER_EXPORTS = {
    "IngestionEventContext",
    "IngestionEventEmitter",
    "DataMigrationEventContext",
    "DataMigrationEventEmitter",
    "LineageEventContext",
    "LineageEventEmitter",
    "PublishEventContext",
    "PublishEventEmitter",
    "QualityResultEventContext",
    "QualityResultEventEmitter",
    "SchemaMigrationEventContext",
    "SchemaMigrationEventEmitter",
    "ServiceLifecycleEventContext",
    "ServiceLifecycleEventEmitter",
    "TelemetryEventContext",
    "TelemetryEventEmitter",
    "TransformEventContext",
    "TransformEventEmitter",
}
_EVENT_EXPORTS = {
    "EVENT_VERSION",
    "HookCorrelation",
    "HookEvent",
    "IngestionEvent",
    "DataMigrationEvent",
    "LineageEvent",
    "PublishEvent",
    "QualityResultEvent",
    "SchemaMigrationEvent",
    "ServiceLifecycleEvent",
    "TelemetryEvent",
    "TransformEvent",
    "LogEvent",
}


if TYPE_CHECKING:
    from phlo.hooks.bus import HookBus, get_hook_bus
    from phlo.hooks.emitters import (
        DataMigrationEventContext,
        DataMigrationEventEmitter,
        IngestionEventContext,
        IngestionEventEmitter,
        LineageEventContext,
        LineageEventEmitter,
        PublishEventContext,
        PublishEventEmitter,
        QualityResultEventContext,
        QualityResultEventEmitter,
        SchemaMigrationEventContext,
        SchemaMigrationEventEmitter,
        ServiceLifecycleEventContext,
        ServiceLifecycleEventEmitter,
        TelemetryEventContext,
        TelemetryEventEmitter,
        TransformEventContext,
        TransformEventEmitter,
    )
    from phlo.hooks.events import (
        EVENT_VERSION,
        DataMigrationEvent,
        HookCorrelation,
        HookEvent,
        IngestionEvent,
        LineageEvent,
        LogEvent,
        PublishEvent,
        QualityResultEvent,
        SchemaMigrationEvent,
        ServiceLifecycleEvent,
        TelemetryEvent,
        TransformEvent,
    )


def __getattr__(name: str):  # noqa: ANN001
    """Lazily resolve exports from hook submodules.

    Args:
        name: Export name requested from this module.

    Returns:
        Exported attribute resolved from bus, emitters, or events modules.

    Raises:
        AttributeError: If name is not an exported hook symbol.

    """
    if name in _BUS_EXPORTS:
        _bus = import_module("phlo.hooks.bus")
        return getattr(_bus, name)
    if name in _EMITTER_EXPORTS:
        _emitters = import_module("phlo.hooks.emitters")
        return getattr(_emitters, name)
    if name in _EVENT_EXPORTS:
        _events = import_module("phlo.hooks.events")
        return getattr(_events, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return module attribute names for introspection tools."""
    return sorted(set(__all__))
