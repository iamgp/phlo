# CoreTelemetryHookProvider (/docs/python-reference/core/phlo/hooks/telemetry/CoreTelemetryHookProvider)



Record generic telemetry events without an external package.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(self) -> None:
        self._recorder = TelemetryRecorder()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> list[HookRegistration]&#x22;">
  <PySourceCode>
    ```python
    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="core_telemetry",
                handler=self._handle_telemetry,
                filters=HookFilter(event_types={"telemetry.log", "telemetry.metric"}),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.plugins.hooks.HookRegistration]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_handle_telemetry&#x22;" type="&#x22;(self, event) -> None&#x22;">
  <PySourceCode>
    ```python
    def _handle_telemetry(self, event: Any) -> None:
        if isinstance(event, TelemetryEvent):
            self._recorder.record(event)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
