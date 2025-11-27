"""PagerDuty alert destination."""

from __future__ import annotations

import logging

import requests

from phlo.alerting.manager import Alert, AlertDestination, AlertSeverity

logger = logging.getLogger(__name__)


class PagerDutyAlertDestination(AlertDestination):
    """Send alerts to PagerDuty via Events API."""

    def __init__(self, integration_key: str):
        """
        Initialize PagerDuty destination.

        Args:
            integration_key: PagerDuty Events API v2 integration key
        """
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def send(self, alert: Alert) -> bool:
        """Send alert to PagerDuty."""
        try:
            payload = self._build_payload(alert)
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 202  # Accepted
        except Exception as e:
            logger.exception(f"Failed to send PagerDuty alert: {e}")
            return False

    def _build_payload(self, alert: Alert) -> dict:
        """Build PagerDuty event payload."""
        # Map severity to PagerDuty severity
        severity_map = {
            AlertSeverity.INFO: "info",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "error",
            AlertSeverity.CRITICAL: "critical",
        }

        pd_severity = severity_map.get(alert.severity, "error")

        # Build custom details
        custom_details = {
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
        }

        if alert.asset_name:
            custom_details["asset"] = alert.asset_name

        if alert.run_id:
            custom_details["run_id"] = alert.run_id

        if alert.error_message:
            custom_details["error"] = alert.error_message

        # Generate dedup key for alert grouping
        dedup_key = f"phlo-{alert.asset_name or 'unknown'}-{alert.run_id or 'unknown'}"

        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": alert.title,
                "severity": pd_severity,
                "source": "Phlo",
                "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
                "custom_details": custom_details,
            },
        }

        return payload
