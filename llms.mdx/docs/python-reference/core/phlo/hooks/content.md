# hooks (/docs/python-reference/core/phlo/hooks)



Hook event system for Phlo plugins.

The hook system provides an event-driven architecture for plugin communication.
Plugins can emit events during various lifecycle stages (ingestion, transformation,
quality checks, etc.) and other plugins can register handlers to react to these
events.

This module uses lazy loading to prevent circular imports during plugin discovery.
All exports are resolved on first access via `__getattr__` to avoid loading
submodules at import time.

Key Components:

* :class:`~phlo.hooks.bus.HookBus`: Central event dispatcher
* :class:`~phlo.hooks.events.HookEvent`: Base event payload
* :class:`~phlo.hooks.emitters.IngestionEventEmitter`: Ingestion lifecycle events
* :class:`~phlo.hooks.emitters.TransformEventEmitter`: Transform lifecycle events
* :class:`~phlo.hooks.emitters.QualityResultEventEmitter`: Quality check events

Event Types:
The system supports multiple event types for different lifecycle stages:

* `ingestion.start`, `ingestion.end`: Ingestion operations
* `transform.start`, `transform.end`: dbt transformations
* `quality.result`: Data quality check results
* `service.start`, `service.stop`: Service lifecycle
* `schema_migration.applied`, `data_migration.completed`: Migrations

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
cycles during plugin discovery. Exports are resolved lazily via `__getattr__`.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['EVENT_VERSION', 'HookBus', 'HookCorrelation', 'HookEvent', 'IngestionEventContext', 'IngestionEventEmitter', 'DataMigrationEventContext', 'DataMigrationEventEmitter', 'LineageEventContext', 'LineageEventEmitter', 'PublishEventContext', 'PublishEventEmitter', 'QualityResultEventContext', 'QualityResultEventEmitter', 'SchemaMigrationEventContext', 'SchemaMigrationEventEmitter', 'ServiceLifecycleEventContext', 'ServiceLifecycleEventEmitter', 'TelemetryEventContext', 'TelemetryEventEmitter', 'TransformEventContext', 'TransformEventEmitter', 'IngestionEvent', 'DataMigrationEvent', 'LineageEvent', 'PublishEvent', 'QualityResultEvent', 'SchemaMigrationEvent', 'ServiceLifecycleEvent', 'TelemetryEvent', 'TransformEvent', 'LogEvent', 'get_hook_bus']&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;__getattr__&#x22;" type="&#x22;(name)&#x22;">
      Lazily resolve exports from hook submodules.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Export name requested from this module.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        Exported attribute resolved from bus, emitters, or events modules.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;__dir__&#x22;" type="&#x22;() -> list[str]&#x22;">
      Return module attribute names for introspection tools.

      <PySourceCode>
        ```python
        def __dir__() -> list[str]:
            """Return module attribute names for introspection tools."""
            return sorted(set(__all__))
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/hooks/telemetry&#x22;" title="&#x22;telemetry&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/hooks/bus&#x22;" title="&#x22;bus&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/hooks/emitters&#x22;" title="&#x22;emitters&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/hooks/events&#x22;" title="&#x22;events&#x22;" />
    </Cards>
  </Tab>
</Tabs>
