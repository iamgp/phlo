# SchemaMigrationEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/SchemaMigrationEventEmitter)



Emit schema migration lifecycle events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the schema migration event emitter.

  <PySourceCode>
    ```python
    def __init__(
        self,
        context: SchemaMigrationEventContext,
        hook_bus: HookBus | None = None,
    ) -> None:
        """Initialize the schema migration event emitter.

        Args:
            context: Shared schema migration context for each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;SchemaMigrationEventContext&#x22;" value="undefined">
      Shared schema migration context for each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit&#x22;" type="&#x22;(self, *, status, classification, change_count, changes=None) -> None&#x22;">
  Emit a schema migration event.

  <PySourceCode>
    ```python
    def emit(
        self,
        *,
        status: str,
        classification: str,
        change_count: int,
        changes: list[dict[str, Any]] | None = None,
    ) -> None:
        """Emit a schema migration event.

        Args:
            status: Lifecycle status (planned, approved, applied, rejected).
            classification: Worst classification across changes.
            change_count: Number of schema changes in the plan.
            changes: Optional list of change detail dicts.

        """
        self._hook_bus.emit(
            SchemaMigrationEvent(
                event_type=f"schema_migration.{status}",
                table_name=self._context.table_name,
                classification=classification,
                change_count=change_count,
                status=status,
                changes=changes or [],
                tags=self._context.tags.copy(),
                correlation=_merge_correlation(base=self._context.correlation),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="undefined">
      Lifecycle status (planned, approved, applied, rejected).
    </PyParameter>

    <PyParameter name="&#x22;classification&#x22;" type="&#x22;str&#x22;" value="undefined">
      Worst classification across changes.
    </PyParameter>

    <PyParameter name="&#x22;change_count&#x22;" type="&#x22;int&#x22;" value="undefined">
      Number of schema changes in the plan.
    </PyParameter>

    <PyParameter name="&#x22;changes&#x22;" type="&#x22;list[dict[str, Any]] | None&#x22;" value="&#x22;None&#x22;">
      Optional list of change detail dicts.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
