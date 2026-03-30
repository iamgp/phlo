# AlertSink (/docs/python-reference/core/phlo/capabilities/interfaces/AlertSink)



Protocol for alerting providers used by orchestrators and APIs.

Functions [#functions]

<PyFunction name="&#x22;send_alert&#x22;" type="&#x22;(self, *, title, message, severity=None, asset_name=None, run_id=None, error_message=None) -> bool&#x22;">
  Send one alert notification.

  <PySourceCode>
    ```python
    def send_alert(
        self,
        *,
        title: str,
        message: str,
        severity: str | None = None,
        asset_name: str | None = None,
        run_id: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Send one alert notification."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;error_message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
