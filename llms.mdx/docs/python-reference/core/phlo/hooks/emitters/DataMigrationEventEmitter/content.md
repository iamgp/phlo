# DataMigrationEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/DataMigrationEventEmitter)



Emit data migration lifecycle events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the data migration event emitter.

  <PySourceCode>
    ```python
    def __init__(
        self,
        context: DataMigrationEventContext,
        hook_bus: HookBus | None = None,
    ) -> None:
        """Initialize the data migration event emitter."""
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;DataMigrationEventContext&#x22;" value="null" />

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit&#x22;" type="&#x22;(self, *, status, rows_read, rows_written, chunk_index, metrics=None) -> None&#x22;">
  Emit a data migration event.

  <PySourceCode>
    ```python
    def emit(
        self,
        *,
        status: str,
        rows_read: int,
        rows_written: int,
        chunk_index: int | None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """Emit a data migration event."""
        tags = self._context.tags.copy()
        tags["source_type"] = self._context.source_type
        tags["destination_table"] = self._context.destination_table
        self._hook_bus.emit(
            DataMigrationEvent(
                event_type=f"data_migration.{status}",
                migration_name=self._context.migration_name,
                source_type=self._context.source_type,
                destination_table=self._context.destination_table,
                status=status,
                rows_read=rows_read,
                rows_written=rows_written,
                chunk_index=chunk_index,
                metrics=metrics or {},
                tags=tags,
                correlation=_merge_correlation(
                    base=self._context.correlation,
                    overrides={"run_id": self._context.run_id},
                ),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;rows_read&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;rows_written&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;chunk_index&#x22;" type="&#x22;int | None&#x22;" value="null" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
