# TelemetryEventEmitter (/docs/python-reference/core/phlo/hooks/emitters/TelemetryEventEmitter)



Emit telemetry events with a shared context.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, hook_bus=None) -> None&#x22;">
  Initialize the telemetry event emitter.

  <PySourceCode>
    ```python
    def __init__(self, context: TelemetryEventContext, hook_bus: HookBus | None = None) -> None:
        """Initialize the telemetry event emitter.

        Args:
            context: Shared telemetry context to include in each emitted event.
            hook_bus: Hook bus used to publish events. Defaults to the global bus.

        """
        self._context = context
        self._hook_bus = hook_bus or get_hook_bus()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;TelemetryEventContext&#x22;" value="undefined">
      Shared telemetry context to include in each emitted event.
    </PyParameter>

    <PyParameter name="&#x22;hook_bus&#x22;" type="&#x22;HookBus | None&#x22;" value="&#x22;None&#x22;">
      Hook bus used to publish events. Defaults to the global bus.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_metric&#x22;" type="&#x22;(self, *, name, value=None, unit=None, payload=None) -> None&#x22;">
  Emit a telemetry metric event.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit_log&#x22;" type="&#x22;(self, *, name, level, value=None, unit=None, payload=None) -> None&#x22;">
  Emit a telemetry log event.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_emit&#x22;" type="&#x22;(self, *, event_type, name, value, level, unit, payload) -> None&#x22;">
  Emit a telemetry event.

  <PySourceCode>
    ```python
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
        """Emit a telemetry event.

        Args:
            event_type: Event type identifier.
            name: Metric or log name.
            value: Optional metric or log value.
            level: Optional log level for log events.
            unit: Optional unit for the value.
            payload: Optional event payload.

        """
        self._hook_bus.emit(
            TelemetryEvent(
                event_type=event_type,
                name=name,
                value=value,
                level=level,
                unit=unit,
                payload=payload or {},
                tags=self._context.tags.copy(),
                correlation=_merge_correlation(base=self._context.correlation),
            )
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Event type identifier.
    </PyParameter>

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Metric or log name.
    </PyParameter>

    <PyParameter name="&#x22;value&#x22;" type="&#x22;Any | None&#x22;" value="undefined">
      Optional metric or log value.
    </PyParameter>

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional log level for log events.
    </PyParameter>

    <PyParameter name="&#x22;unit&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional unit for the value.
    </PyParameter>

    <PyParameter name="&#x22;payload&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="undefined">
      Optional event payload.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
