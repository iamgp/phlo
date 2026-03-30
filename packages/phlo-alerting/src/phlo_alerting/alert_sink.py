"""Neutral alert-sink wrapper over the alerting manager.

This module provides the AlertManagerSink class, which implements the
neutral alert-sink capability interface. It wraps the AlertManager to
provide a standardized way for external systems to send alerts through
phlo-alerting without direct dependencies on the manager internals.
"""

from __future__ import annotations

from datetime import datetime, timezone

from phlo_alerting.manager import Alert, AlertSeverity, get_alert_manager


class AlertManagerSink:
    """Expose phlo-alerting through the neutral alert-sink capability.

        This class implements the alert sink interface expected by the Phlo
    capability system. It translates external alert calls into the internal
    Alert format and routes them through the shared AlertManager.

    Examples:
            >>> sink = AlertManagerSink()
            >>> sink.send_alert(
            ...     title="Test Alert",
            ...     message="This is a test",
            ...     severity="error"
            ... )

    Attributes:
            None; this class is stateless and delegates to AlertManager.

    """

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
