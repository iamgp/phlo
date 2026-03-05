"""Dagster sensors for automated alerting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from dagster import DagsterEventType, DagsterRunStatus, RunsFilter, sensor

from phlo.logging import get_logger

logger = get_logger(__name__)


def _load_alerting() -> tuple[type[Any], type[Any], Any]:
    """Load alerting classes lazily so base package works without phlo-alerting."""
    try:
        from phlo_alerting.manager import Alert, AlertSeverity, get_alert_manager
    except Exception as exc:  # noqa: BLE001 - provide actionable runtime error
        raise RuntimeError(
            "Alerting integration requires phlo-alerting. Install phlo-dagster[alerting] "
            "or phlo-alerting."
        ) from exc
    return Alert, AlertSeverity, get_alert_manager


@sensor(
    name="failure_alert_sensor",
    description="Send alerts on run failures",
    minimum_interval_seconds=300,  # Check every 5 minutes
)
def failure_alert_sensor(context):
    """
    Sensor that triggers alerts when asset materializations fail.

    Uses cursor to track the last-seen run creation time cutoff to avoid
    re-alerting across sensor ticks.
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
        Alert, AlertSeverity, get_alert_manager = _load_alerting()
        # Query for failed runs created after the cursor cutoff
        failed_runs = list(
            instance.get_runs(
                filters=RunsFilter(
                    statuses=[DagsterRunStatus.FAILURE],
                    updated_after=cutoff_time,
                )
            )
        )

        alert_manager = get_alert_manager()

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


def _extract_error_message(event) -> str | None:
    """Extract error message from event."""
    if hasattr(event, "step_output_event"):
        return event.step_output_event.get("error")
    return None


# Convenience function for applications to send custom alerts
def send_alert(
    title: str,
    message: str,
    severity: Any = "ERROR",
    asset_name: str | None = None,
    run_id: str | None = None,
    error_message: str | None = None,
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
    Alert, AlertSeverity, get_alert_manager = _load_alerting()
    severity_value = _coerce_alert_severity(severity, AlertSeverity)
    alert_manager = get_alert_manager()
    alert = Alert(
        title=title,
        message=message,
        severity=severity_value,
        asset_name=asset_name,
        run_id=run_id,
        error_message=error_message,
        timestamp=datetime.now(timezone.utc),
    )
    return alert_manager.send(alert)


def _coerce_alert_severity(severity: Any, alert_severity_type: type[Any]) -> Any:
    """Normalize user-provided severity into the alert severity enum."""
    if isinstance(severity, alert_severity_type):
        return severity
    if isinstance(severity, str):
        normalized = severity.strip()
        if not normalized:
            return alert_severity_type.ERROR
        by_name = getattr(alert_severity_type, normalized.upper(), None)
        if by_name is not None:
            return by_name
        if issubclass(alert_severity_type, Enum):
            try:
                return alert_severity_type(normalized.lower())
            except ValueError:
                return alert_severity_type.ERROR
        return alert_severity_type.ERROR
    return alert_severity_type.ERROR
