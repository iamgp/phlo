"""Dagster sensors for automated alerting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from dagster import DagsterEventType, sensor

from phlo.logging import get_logger
from phlo_alerting.manager import Alert, AlertSeverity, get_alert_manager

logger = get_logger(__name__)


@sensor(
    name="failure_alert_sensor",
    description="Send alerts on run failures",
    minimum_interval_seconds=300,  # Check every 5 minutes
)
def failure_alert_sensor(context):
    """
    Sensor that triggers alerts when asset materializations fail.

    Checks for failed runs in the last 5 minutes and sends alerts
    to configured destinations (Slack, PagerDuty, Email).
    """
    # Get the Dagster instance
    instance = context.instance

    # Look for failed runs in the last 5 minutes
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    # Query for failed runs
    failed_runs = list(
        instance.get_runs(
            filters={
                # Filter for failed runs since cutoff
                "status": "FAILURE",
                "created_at_after": cutoff_time,
            }
        )
    )

    alert_manager = get_alert_manager()

    for run in failed_runs:
        # Skip if already alerted
        alert_key = f"run_{run.run_id}"
        if hasattr(context, "_alerted_runs") and alert_key in context._alerted_runs:
            continue

        # Get run events to find failures
        events = instance.get_event_log_entries(
            run_id=run.run_id,
            event_filter_fn=lambda event: event.event_type == DagsterEventType.PIPELINE_FAILURE,
        )

        for event in events:
            # Build alert
            alert = Alert(
                title=f"Pipeline Run Failed: {run.job_name}",
                message=f"Run {run.run_id} for job {run.job_name} has failed",
                severity=AlertSeverity.ERROR,
                asset_name=run.job_name,
                run_id=run.run_id,
                error_message=_extract_error_message(event),
                timestamp=datetime.now(timezone.utc),
            )

            # Send alert
            if alert_manager.send(alert):
                logger.info(f"Sent failure alert for run {run.run_id}")

                # Mark as alerted
                if not hasattr(context, "_alerted_runs"):
                    context._alerted_runs = set()
                context._alerted_runs.add(alert_key)


def _extract_error_message(event) -> Optional[str]:
    """Extract error message from event."""
    if hasattr(event, "step_output_event"):
        return event.step_output_event.get("error")
    return None


# Convenience function for applications to send custom alerts
def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.ERROR,
    asset_name: Optional[str] = None,
    run_id: Optional[str] = None,
    error_message: Optional[str] = None,
) -> bool:
    """
    Send a custom alert.

    Args:
        title: Alert title
        message: Alert message
        severity: Alert severity (default: ERROR)
        asset_name: Optional asset name
        run_id: Optional run ID
        error_message: Optional detailed error message

    Returns:
        True if alert was sent successfully
    """
    alert_manager = get_alert_manager()
    alert = Alert(
        title=title,
        message=message,
        severity=severity,
        asset_name=asset_name,
        run_id=run_id,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc),
    )
    return alert_manager.send(alert)
