# IngestionEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/IngestionEventEmitter)



Emit ingestion lifecycle events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the ingestion event emitter.

  <PySourceCode>
    ```python
    def __init__(self, context: IngestionEventContext, hook_bus: HookBus | None = None) -> None:
        """Initialize the ingestion event emitter.

        Args:
            context: Shared ingestion context to include in each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;IngestionEventContext&#x22;" value="undefined">
      Shared ingestion context to include in each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_start&#x22;" type="&#x22;(self, *, status='started') -> None&#x22;">
  Emit an ingestion start event.

  <PySourceCode>
    ```python
    def emit_start(self, *, status: str = "started") -> None:
        """Emit an ingestion start event."""
        self._emit(event_type="ingestion.start", status=status, metrics=None, error=None)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;'started'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_end&#x22;" type="&#x22;(self, *, status, metrics=None, error=None) -> None&#x22;">
  Emit an ingestion end event.

  <PySourceCode>
    ```python
    def emit_end(
        self,
        *,
        status: str,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Emit an ingestion end event."""
        self._emit(event_type="ingestion.end", status=status, metrics=metrics, error=error)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_emit&#x22;" type="&#x22;(self, *, event_type, status, metrics, error) -> None&#x22;">
  Emit an ingestion event.

  <PySourceCode>
    ```python
    def _emit(
        self,
        *,
        event_type: str,
        status: str | None,
        metrics: dict[str, Any] | None,
        error: str | None,
    ) -> None:
        """Emit an ingestion event.

        Args:
            event_type: Event type identifier.
            status: Lifecycle status value.
            metrics: Optional metric payload.
            error: Optional error message.

        """
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
                correlation=_merge_correlation(
                    base=self._context.correlation,
                    overrides={
                        "run_id": self._context.run_id,
                        "asset_key": self._context.asset_key,
                        "partition_key": self._context.partition_key,
                    },
                ),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Event type identifier.
    </PyParameter>

    <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Lifecycle status value.
    </PyParameter>

    <PyParameter name="&#x22;metrics&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="undefined">
      Optional metric payload.
    </PyParameter>

    <PyParameter name="&#x22;error&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional error message.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
