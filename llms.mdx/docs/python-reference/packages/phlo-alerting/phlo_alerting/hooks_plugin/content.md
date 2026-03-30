# hooks_plugin (/docs/python-reference/packages/phlo-alerting/phlo_alerting/hooks_plugin)



Hook plugin for alerting on quality and telemetry events.

This module implements the HookPlugin interface to automatically trigger
alerts based on Phlo pipeline events. It monitors quality check results
and telemetry events, sending notifications when issues are detected.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;AlertingHookPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/hooks_plugin/AlertingHookPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_map_quality_severity&#x22;" type="&#x22;(severity) -> AlertSeverity&#x22;">
      Map quality severity strings to alert severities.

      Converts quality check severity strings into AlertSeverity enum values.
      Handles various quality severity formats including "WARN", "CRITICAL",
      and "FATAL".

      <PySourceCode>
        ```python
        def _map_quality_severity(severity: str | None) -> AlertSeverity:
            """Map quality severity strings to alert severities.

            Converts quality check severity strings into AlertSeverity enum values.
            Handles various quality severity formats including "WARN", "CRITICAL",
            and "FATAL".

            Args:
                severity: Quality severity string or None.

            Returns:
                AlertSeverity corresponding to the input, or ERROR as default.

            Examples:
                >>> _map_quality_severity("WARN")
                <AlertSeverity.WARNING: 'warning'>
                >>> _map_quality_severity("CRITICAL")
                <AlertSeverity.CRITICAL: 'critical'>
                >>> _map_quality_severity(None)
                <AlertSeverity.ERROR: 'error'>
                >>> _map_quality_severity("unknown")
                <AlertSeverity.ERROR: 'error'>

            """

            if not severity:
                return AlertSeverity.ERROR
            value = severity.upper()
            if value == "WARN":
                return AlertSeverity.WARNING
            if value in {"CRITICAL", "FATAL"}:
                return AlertSeverity.CRITICAL
            return AlertSeverity.ERROR
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Quality severity string or None.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_alerting.manager.AlertSeverity&#x22;">
        AlertSeverity corresponding to the input, or ERROR as default.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_telemetry_severity&#x22;" type="&#x22;(level) -> AlertSeverity&#x22;">
      Map telemetry levels to alert severities.

      Converts telemetry event levels into AlertSeverity enum values.
      Critical telemetry events become CRITICAL alerts, all other
      error levels become ERROR alerts.

      <PySourceCode>
        ```python
        def _map_telemetry_severity(level: str) -> AlertSeverity:
            """Map telemetry levels to alert severities.

                Converts telemetry event levels into AlertSeverity enum values.
                Critical telemetry events become CRITICAL alerts, all other
            error levels become ERROR alerts.

            Args:
                    level: Telemetry level string (e.g., "error", "critical").

            Returns:
                    AlertSeverity corresponding to the telemetry level.

            Examples:
                    >>> _map_telemetry_severity("critical")
                    <AlertSeverity.CRITICAL: 'critical'>
                    >>> _map_telemetry_severity("error")
                    <AlertSeverity.ERROR: 'error'>

            """

            value = level.lower()
            if value == "critical":
                return AlertSeverity.CRITICAL
            return AlertSeverity.ERROR
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="undefined">
          Telemetry level string (e.g., "error", "critical").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_alerting.manager.AlertSeverity&#x22;">
        AlertSeverity corresponding to the telemetry level.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_format_quality_message&#x22;" type="&#x22;(event) -> str&#x22;">
      Format a human-readable quality failure message.

      Constructs a formatted message string from quality check failure
      details, including asset information, check name, partition key, and
      any available error or failure messages.

      <PySourceCode>
        ```python
        def _format_quality_message(event: QualityResultEvent) -> str:
            """Format a human-readable quality failure message.

                Constructs a formatted message string from quality check failure
            details, including asset information, check name, partition key, and
            any available error or failure messages.

            Args:
                    event: QualityResultEvent containing failure details.

            Returns:
                    Formatted multi-line string with quality failure information.

            Examples:
                    >>> from phlo.hooks import QualityResultEvent
                    >>> event = QualityResultEvent(
                    ...     check_name="null_check",
                    ...     asset_key="users_table",
                    ...     passed=False,
                    ...     partition_key="2024-01-01",
                    ...     metadata={"error": "Null values found", "failure_message": "3 rows failed"}
                    ... )
                    >>> msg = _format_quality_message(event)
                    >>> "Asset: users_table" in msg
                    True
                    >>> "Partition: 2024-01-01" in msg
                    True

            """

            parts = [
                f"Asset: {event.asset_key}",
                f"Check: {event.check_name}",
            ]
            if event.partition_key:
                parts.append(f"Partition: {event.partition_key}")
            if event.metadata.get("error"):
                parts.append(f"Error: {event.metadata['error']}")
            if event.metadata.get("failure_message"):
                parts.append(f"Details: {event.metadata['failure_message']}")
            return "\n".join(parts)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="&#x22;QualityResultEvent&#x22;" value="undefined">
          QualityResultEvent containing failure details.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Formatted multi-line string with quality failure information.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
