# alerting_sensor (/docs/python-reference/packages/phlo-dagster/phlo_dagster/alerting_sensor)



Dagster sensors for automated alerting on pipeline failures.

This module provides Dagster sensors that monitor run events and send alerts
when pipeline failures occur. It integrates with Phlo's alerting capabilities
to provide notifications via configured alert sinks (Slack, PagerDuty, etc.).

Key Features:

* failure\_alert\_sensor: Polls for failed runs and sends alerts
* Automatic error message extraction from run events
* Configurable alert sink resolution
* Deduplication via cursor tracking

Alert Sink Requirements:
Requires an alert\_sink:alerting capability. Install phlo-alerting or another
provider exposing that capability.

Example:
To enable alerting in your Dagster deployment::

from phlo\_dagster.alerting\_sensor import failure\_alert\_sensor

defs = dg.Definitions(
sensors=\[failure\_alert\_sensor],

... other definitions [#-other-definitions]

)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_alert_sink&#x22;" type="&#x22;() -> AlertSink&#x22;">
      Resolve the configured alert sink capability.

      <PySourceCode>
        ```python
        def _load_alert_sink() -> AlertSink:
            """Resolve the configured alert sink capability.

            Args:
                None

            Returns:
                AlertSink provider instance.

            Raises:
                RuntimeError: If alert_sink:alerting capability is not available.

            """
            resolution = resolve_capability("alert_sink", "alerting")
            if resolution is None:
                raise RuntimeError(
                    "Alerting integration requires an alert_sink:alerting capability. "
                    "Install phlo-alerting or another provider exposing that capability."
                )
            return resolution.provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.AlertSink&#x22;">
        AlertSink provider instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;failure_alert_sensor&#x22;" type="&#x22;(context)&#x22;">
      Sensor that triggers alerts when asset materializations fail.

      Uses cursor to track the last-seen run creation time cutoff to avoid
      re-alerting across sensor ticks.

      <PySourceCode>
        ```python
        @sensor(
            name="failure_alert_sensor",
            description="Send alerts on run failures",
            minimum_interval_seconds=300,  # Check every 5 minutes
        )
        def failure_alert_sensor(context):
            """Sensor that triggers alerts when asset materializations fail.

            Uses cursor to track the last-seen run creation time cutoff to avoid
            re-alerting across sensor ticks.

            Args:
                context: Dagster sensor evaluation context.

            Returns:
                None

            Raises:
                Exception: Re-raises any exception during alert processing.

            """
            instance = context.instance

            # Parse cursor as ISO datetime for dedup across ticks
            cutoff_time = None
            if context.cursor:
                try:
                    cutoff_time = datetime.fromisoformat(context.cursor)
                except ValueError:
                    cutoff_time = None

            if cutoff_time is None:
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

            alerted_count = 0
            scanned_event_count = 0

            logger.info(
                "failure_alert_sensor_scan_started",
                cutoff_time=cutoff_time.isoformat(),
            )
            try:
                alert_sink = _load_alert_sink()
                # Query for failed runs created after the cursor cutoff
                failed_runs = list(
                    instance.get_runs(
                        filters=RunsFilter(
                            statuses=[DagsterRunStatus.FAILURE],
                            updated_after=cutoff_time,
                        )
                    )
                )
                for run in failed_runs:
                    # Get run events to find failures
                    events = list(
                        instance.get_event_log_entries(
                            run_id=run.run_id,
                            event_filter_fn=lambda event: (
                                event.event_type == DagsterEventType.PIPELINE_FAILURE
                            ),
                        )
                    )
                    scanned_event_count += len(events)

                    for event in events:
                        # Build alert
                        if alert_sink.send_alert(
                            title=f"Pipeline Run Failed: {run.job_name}",
                            message=f"Run {run.run_id} for job {run.job_name} has failed",
                            severity="ERROR",
                            asset_name=run.job_name,
                            run_id=run.run_id,
                            error_message=_extract_error_message(event),
                        ):
                            alerted_count += 1
                            logger.info("failure_alert_sent", run_id=run.run_id, job_name=run.job_name)

                logger.info(
                    "failure_alert_sensor_scan_completed",
                    cutoff_time=cutoff_time.isoformat(),
                    failed_run_count=len(failed_runs),
                    failure_event_count=scanned_event_count,
                    alerts_sent_count=alerted_count,
                )
            except Exception as exc:
                logger.error(
                    "failure_alert_sensor_scan_failed",
                    cutoff_time=cutoff_time.isoformat(),
                    failure_event_count=scanned_event_count,
                    alerts_sent_count=alerted_count,
                    error=str(exc),
                    exc_info=True,
                )
                raise

            # Advance cursor to now so next tick only sees newer runs
            context.update_cursor(datetime.now(timezone.utc).isoformat())
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="null" value="undefined">
          Dagster sensor evaluation context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_extract_error_message&#x22;" type="&#x22;(event) -> str | None&#x22;">
      Extract error message from event.

      <PySourceCode>
        ```python
        def _extract_error_message(event) -> str | None:
            """Extract error message from event.

            Args:
                event: Dagster event log entry.

            Returns:
                Error message string or None.

            """
            if hasattr(event, "step_output_event"):
                return event.step_output_event.get("error")
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event&#x22;" type="null" value="undefined">
          Dagster event log entry.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Error message string or None.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;send_alert&#x22;" type="&#x22;(title, message, severity='ERROR', asset_name=None, run_id=None, error_message=None) -> bool&#x22;">
      Send a custom alert.

      <PySourceCode>
        ```python
        def send_alert(
            title: str,
            message: str,
            severity: str | None = "ERROR",
            asset_name: str | None = None,
            run_id: str | None = None,
            error_message: str | None = None,
        ) -> bool:
            """Send a custom alert.

            Args:
                title: Alert title.
                message: Alert message.
                severity: Alert severity (default: ERROR).
                asset_name: Optional asset name.
                run_id: Optional run ID.
                error_message: Optional detailed error message.

            Returns:
                True if alert was sent successfully.

            """
            return _load_alert_sink().send_alert(
                title=title,
                message=message,
                severity=severity,
                asset_name=asset_name,
                run_id=run_id,
                error_message=error_message,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="undefined">
          Alert title.
        </PyParameter>

        <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
          Alert message.
        </PyParameter>

        <PyParameter name="&#x22;severity&#x22;" type="&#x22;str | None&#x22;" value="&#x22;'ERROR'&#x22;">
          Alert severity (default: ERROR).
        </PyParameter>

        <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional asset name.
        </PyParameter>

        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional run ID.
        </PyParameter>

        <PyParameter name="&#x22;error_message&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional detailed error message.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if alert was sent successfully.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
