# AlertManagerSink (/docs/python-reference/packages/phlo-alerting/phlo_alerting/alert_sink/AlertManagerSink)



Expose phlo-alerting through the neutral alert-sink capability.

This class implements the alert sink interface expected by the Phlo
capability system. It translates external alert calls into the internal
Alert format and routes them through the shared AlertManager.

Functions [#functions]

<PyFunction name="&#x22;send_alert&#x22;" type="&#x22;(self, *, title, message, severity=None, asset_name=None, run_id=None, error_message=None) -> bool&#x22;">
  Send one alert through the shared alert manager.

  This method creates an Alert object from the provided parameters
  and routes it through the global AlertManager to all configured
  destinations.

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
        """Send one alert through the shared alert manager.

                This method creates an Alert object from the provided parameters
                and routes it through the global AlertManager to all configured
        destinations.

        Args:
                    title: Short alert title or summary.
                    message: Detailed alert message or description.
                    severity: Alert severity level as string (info, warning, error, critical).
                        Defaults to "error" if not provided or invalid.
                    asset_name: Optional name of the asset that triggered the alert.
                    run_id: Optional run identifier for correlation.
                    error_message: Optional detailed error message or stack trace.

        Returns:
                    True if the alert was sent successfully to at least one destination,
                    False otherwise.

        Raises:
                    None; exceptions from individual destinations are logged but not raised.

        Examples:
                    >>> sink = AlertManagerSink()
                    >>> result = sink.send_alert(
                    ...     title="Pipeline Error",
                    ...     message="ETL job failed",
                    ...     severity="critical",
                    ...     asset_name="sales_data",
                    ...     run_id="run_123"
                    ... )
                    >>> isinstance(result, bool)
                    True

        """
        alert = Alert(
            title=title,
            message=message,
            severity=_coerce_alert_severity(severity),
            asset_name=asset_name,
            run_id=run_id,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc),
        )
        return get_alert_manager().send(alert)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="undefined">
      Short alert title or summary.
    </PyParameter>

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Detailed alert message or description.
    </PyParameter>

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Alert severity level as string (info, warning, error, critical).
      Defaults to "error" if not provided or invalid.
    </PyParameter>

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional name of the asset that triggered the alert.
    </PyParameter>

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional run identifier for correlation.
    </PyParameter>

    <PyParameter name="&#x22;error_message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional detailed error message or stack trace.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the alert was sent successfully to at least one destination,
  </PyFunctionReturn>
</PyFunction>
