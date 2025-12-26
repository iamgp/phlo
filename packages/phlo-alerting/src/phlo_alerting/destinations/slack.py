"""Slack alert destination."""

from __future__ import annotations

import logging
from typing import Optional

import requests

from phlo_alerting.manager import Alert, AlertDestination, AlertSeverity

logger = logging.getLogger(__name__)


class SlackAlertDestination(AlertDestination):
    """Send alerts to Slack via webhook."""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """
        Initialize Slack destination.

        Args:
            webhook_url: Slack incoming webhook URL
            channel: Optional channel to override (e.g., #alerts)
        """
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            payload = self._build_payload(alert)
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.exception(f"Failed to send Slack alert: {e}")
            return False

    def _build_payload(self, alert: Alert) -> dict:
        """Build Slack message payload."""
        # Color based on severity
        severity_colors = {
            AlertSeverity.INFO: "#36a64f",  # Green
            AlertSeverity.WARNING: "#ff9900",  # Orange
            AlertSeverity.ERROR: "#ff3333",  # Red
            AlertSeverity.CRITICAL: "#cc0000",  # Dark red
        }

        color = severity_colors.get(alert.severity, "#999999")

        # Build message blocks
        fields = [
            {
                "title": "Severity",
                "value": alert.severity.value.upper(),
                "short": True,
            },
            {
                "title": "Time",
                "value": alert.timestamp.isoformat() if alert.timestamp else "N/A",
                "short": True,
            },
        ]

        if alert.asset_name:
            fields.append(
                {
                    "title": "Asset",
                    "value": alert.asset_name,
                    "short": True,
                }
            )

        if alert.run_id:
            fields.append(
                {
                    "title": "Run ID",
                    "value": alert.run_id[:8],
                    "short": True,
                }
            )

        # Build attachment
        attachment = {
            "color": color,
            "title": alert.title,
            "text": alert.message,
            "fields": fields,
        }

        if alert.error_message:
            attachment["fields"].append(
                {
                    "title": "Error",
                    "value": f"```{alert.error_message[:500]}```",
                    "short": False,
                }
            )

        payload = {
            "attachments": [attachment],
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload
