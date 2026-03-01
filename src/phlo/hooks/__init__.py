"""Hook bus for capability plugins.

This module intentionally avoids importing submodules at import time to prevent
cycles during plugin discovery. Exports are resolved lazily via __getattr__.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "EVENT_VERSION",
    "HookBus",
    "HookEvent",
    "IngestionEventContext",
    "IngestionEventEmitter",
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
    "HookEvent",
    "IngestionEvent",
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
        from phlo.hooks import bus as _bus

        return getattr(_bus, name)
    if name in _EMITTER_EXPORTS:
        from phlo.hooks import emitters as _emitters

        return getattr(_emitters, name)
    if name in _EVENT_EXPORTS:
        from phlo.hooks import events as _events

        return getattr(_events, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return module attribute names for introspection tools."""

    return sorted(set(__all__))
