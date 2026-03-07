"""Neutral alert-sink wrapper over the alerting manager."""

from __future__ import annotations

from datetime import datetime, timezone

from phlo_alerting.manager import Alert, AlertSeverity, get_alert_manager


class AlertManagerSink:
    """Expose phlo-alerting through the neutral alert-sink capability."""

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
        """Send one alert through the shared alert manager."""
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


def _coerce_alert_severity(severity: str | None) -> AlertSeverity:
    """Normalize string severity into the alerting enum."""
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
