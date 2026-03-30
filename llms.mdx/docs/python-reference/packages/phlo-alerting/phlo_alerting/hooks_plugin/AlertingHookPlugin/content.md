# AlertingHookPlugin (/docs/python-reference/packages/phlo-alerting/phlo_alerting/hooks_plugin/AlertingHookPlugin)



Emit alerts based on quality and telemetry events.

Hook plugin implementation that listens to Phlo pipeline events and
automatically sends alerts when quality checks fail or error-level
telemetry events occur. Integrates with the AlertManager to route
notifications to configured destinations.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identity and discovery information.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> list[HookRegistration]&#x22;">
  Register quality and telemetry hook handlers.

  Returns a list of HookRegistration objects defining which events
  this plugin handles and the corresponding handler methods.

  <PySourceCode>
    ```python
    def get_hooks(self) -> list[HookRegistration]:
        """Register quality and telemetry hook handlers.

        Returns a list of HookRegistration objects defining which events
        this plugin handles and the corresponding handler methods.

        Returns:
            List of HookRegistration objects for quality and telemetry events.

        Examples:
            >>> plugin = AlertingHookPlugin()
            >>> hooks = plugin.get_hooks()
            >>> [h.hook_name for h in hooks]
            ['alerting_quality', 'alerting_telemetry']

        """

        return [
            HookRegistration(
                hook_name="alerting_quality",
                handler=self._handle_quality,
                filters=HookFilter(event_types={"quality.result"}),
            ),
            HookRegistration(
                hook_name="alerting_telemetry",
                handler=self._handle_telemetry,
                filters=HookFilter(event_types={"telemetry.log", "telemetry.metric"}),
            ),
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of HookRegistration objects for quality and telemetry events.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_quality&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Send an alert for failed quality checks.

  Event handler for quality check results. Only processes events
  of type QualityResultEvent that have failed (passed=False).
  Maps quality severity levels to alert severities and formats
  a human-readable message.

  <PySourceCode>
    ```python
    def _handle_quality(self, event: Any) -> None:
        """Send an alert for failed quality checks.

        Event handler for quality check results. Only processes events
        of type QualityResultEvent that have failed (passed=False).
        Maps quality severity levels to alert severities and formats
        a human-readable message.

        Args:
            event: The quality result event to process. Expected to be
                a QualityResultEvent instance.

        Returns:
            None

        Raises:
            None; exceptions are caught and logged by the hook system.

        Examples:
            This method is called automatically by the Phlo hook system
            when quality.result events are emitted.

        """

        if not isinstance(event, QualityResultEvent):
            return
        if event.passed:
            return
        severity = _map_quality_severity(event.severity)
        message = _format_quality_message(event)
        alert = Alert(
            title=f"Quality check failed: {event.check_name}",
            message=message,
            severity=severity,
            asset_name=event.asset_key,
        )
        logger.info(
            "alerting_quality_alert_send",
            event_type=event.event_type,
            asset_key=event.asset_key,
            check_name=event.check_name,
            quality_severity=event.severity,
            alert_severity=severity.value,
        )
        get_alert_manager().send(alert)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The quality result event to process. Expected to be
      a QualityResultEvent instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_telemetry&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Send an alert for error-level telemetry events.

  Event handler for telemetry events. Only processes events of
  type TelemetryEvent with level "error" or "critical". Maps telemetry
  levels to alert severities and extracts asset information from tags.

  <PySourceCode>
    ```python
    def _handle_telemetry(self, event: Any) -> None:
        """Send an alert for error-level telemetry events.

                Event handler for telemetry events. Only processes events of
        type TelemetryEvent with level "error" or "critical". Maps telemetry
                levels to alert severities and extracts asset information from tags.

        Args:
                    event: The telemetry event to process. Expected to be a
                        TelemetryEvent instance with error or critical level.

        Returns:
                    None

        Raises:
                    None; exceptions are caught and logged by the hook system.

        Examples:
                    This method is called automatically by the Phlo hook system
                    when telemetry.log or telemetry.metric events are emitted.

        """

        if not isinstance(event, TelemetryEvent):
            return
        if not event.level or event.level.lower() not in {"error", "critical"}:
            return
        alert = Alert(
            title=f"Telemetry {event.level} event: {event.name}",
            message=str(event.payload or event.value or ""),
            severity=_map_telemetry_severity(event.level),
            asset_name=event.tags.get("asset"),
        )
        logger.info(
            "alerting_telemetry_alert_send",
            event_type=event.event_type,
            event_name=event.name,
            level=event.level.lower(),
            asset_key=event.tags.get("asset"),
            alert_severity=alert.severity.value,
        )
        get_alert_manager().send(alert)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      The telemetry event to process. Expected to be a
      TelemetryEvent instance with error or critical level.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>
