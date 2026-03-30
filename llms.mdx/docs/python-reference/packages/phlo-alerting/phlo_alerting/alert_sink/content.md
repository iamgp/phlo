# alert_sink (/docs/python-reference/packages/phlo-alerting/phlo_alerting/alert_sink)



Neutral alert-sink wrapper over the alerting manager.

This module provides the AlertManagerSink class, which implements the
neutral alert-sink capability interface. It wraps the AlertManager to
provide a standardized way for external systems to send alerts through
phlo-alerting without direct dependencies on the manager internals.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;AlertManagerSink&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/alert_sink/AlertManagerSink&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_coerce_alert_severity&#x22;" type="&#x22;(severity) -> AlertSeverity&#x22;">
      Normalize string severity into the alerting enum.

      Converts string severity values into AlertSeverity enum values.
      Handles case insensitivity and provides fallback to ERROR for
      invalid or missing values.

      <PySourceCode>
        ```python
        def _coerce_alert_severity(severity: str | None) -> AlertSeverity:
            """Normalize string severity into the alerting enum.

            Converts string severity values into AlertSeverity enum values.
            Handles case insensitivity and provides fallback to ERROR for
            invalid or missing values.

            Args:
                severity: String severity value or None.

            Returns:
                AlertSeverity enum value matching the input, or AlertSeverity.ERROR
                if the input is None, empty, or invalid.

            Examples:
                >>> _coerce_alert_severity("warning")
                <AlertSeverity.WARNING: 'warning'>
                >>> _coerce_alert_severity("CRITICAL")
                <AlertSeverity.CRITICAL: 'critical'>
                >>> _coerce_alert_severity(None)
                <AlertSeverity.ERROR: 'error'>
                >>> _coerce_alert_severity("invalid")
                <AlertSeverity.ERROR: 'error'>

            """
            if not severity:
                return AlertSeverity.ERROR
            normalized = severity.strip()
            if not normalized:
                return AlertSeverity.ERROR
            by_name = getattr(AlertSeverity, normalized.upper(), None)
            if by_name is not None:
                return by_name
            try:
                return AlertSeverity(normalized.lower())
            except ValueError:
                return AlertSeverity.ERROR
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          String severity value or None.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_alerting.manager.AlertSeverity&#x22;">
        AlertSeverity enum value matching the input, or AlertSeverity.ERROR
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
