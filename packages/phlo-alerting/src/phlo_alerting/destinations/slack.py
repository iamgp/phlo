"""Slack alert destination.

This module provides SlackAlertDestination, which sends alerts to Slack
channels via incoming webhooks. Supports rich message formatting with
severity-based colors and structured field layouts.

Configuration is typically loaded from environment variables:
    PHLO_ALERT_SLACK_WEBHOOK: Slack incoming webhook URL
    PHLO_ALERT_SLACK_CHANNEL: Optional channel override (e.g., "#alerts")

Examples:
    Basic usage:
        >>> from phlo_alerting.destinations.slack import SlackAlertDestination
        >>> dest = SlackAlertDestination(
        ...     webhook_url="https://hooks.slack.com/services/T000/B000/XXXX",
        ...     channel="#alerts"
        ... )
        >>> dest.send(alert)
        True

    Creating from environment:
        >>> import os
        >>> webhook = os.environ.get("PHLO_ALERT_SLACK_WEBHOOK")
        >>> dest = SlackAlertDestination(webhook_url=webhook)

See Also:
    manager.AlertDestination: Base class defining the interface.
    settings.AlertingSettings: Configuration model for Slack settings.

"""

from __future__ import annotations

from typing import Optional

import requests

from phlo.logging import get_logger
from phlo_alerting.manager import Alert, AlertDestination, AlertSeverity

logger = get_logger(__name__)


class SlackAlertDestination(AlertDestination):
    """Send alerts to Slack via webhook.

        Concrete implementation of AlertDestination that delivers alerts
    to Slack channels using incoming webhooks. Formats messages as Slack
    attachments with severity-based colors and structured field layouts.

    Attributes:
            webhook_url: Slack incoming webhook URL for posting messages.
            channel: Optional channel override (e.g., "#alerts").

    Examples:
            >>> dest = SlackAlertDestination(
            ...     webhook_url="https://hooks.slack.com/services/...",
            ...     channel="#data-alerts"
            ... )
            >>> isinstance(dest, AlertDestination)
            True

    """

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """Initialize Slack destination.

                Creates a SlackAlertDestination instance configured to send
        messages to the specified webhook URL. The webhook URL must be a
        valid Slack incoming webhook.

        Args:
                    webhook_url: Slack incoming webhook URL obtained from
                        the Slack app configuration (e.g., "https://hooks.slack.com/services/...").
                    channel: Optional channel name to override the webhook's
        default channel (e.g., "#alerts", "@username").

        Returns:
                    None

        Raises:
                    None; URL validation occurs during send().

        Examples:
                    >>> dest = SlackAlertDestination("https://hooks.slack.com/services/...")
                    >>> dest.webhook_url
                    'https://hooks.slack.com/services/...'
                    >>> dest.channel is None
                    True

        """
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: Alert) -> bool:
        """Send alert to Slack.

                Posts the alert to the configured Slack webhook as a message
        attachment with severity-based coloring and structured fields.

        Args:
                    alert: Alert object containing notification details.

        Returns:
                    True if the message was posted successfully (HTTP 200),
                    False otherwise.

        Raises:
                    None; network errors are caught and logged.

        Examples:
                    >>> from phlo_alerting.manager import Alert, AlertSeverity
                    >>> alert = Alert(
                    ...     title="Pipeline Error",
                    ...     message="ETL job failed",
                    ...     severity=AlertSeverity.CRITICAL,
                    ...     asset_name="sales_data"
                    ... )
                    >>> result = dest.send(alert)
                    >>> isinstance(result, bool)
                    True

        """
        try:
            payload = self._build_payload(alert)
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception:
            logger.exception(
                "slack_alert_send_failed",
                alert_title=alert.title,
                severity=alert.severity.value,
                asset_name=alert.asset_name,
                run_id=alert.run_id,
            )
            return False

    def _build_payload(self, alert: Alert) -> dict:
        """Build Slack message payload.

                Constructs a Slack message attachment payload with severity-based
        color coding and structured field layout. Includes asset name, run ID,
                and error details when available.

        Args:
                    alert: Alert object to format.

        Returns:
                    Dictionary representing Slack message payload.

        Examples:
                    >>> from phlo_alerting.manager import Alert, AlertSeverity
                    >>> alert = Alert(
                    ...     title="Test",
                    ...     message="Test message",
                    ...     severity=AlertSeverity.WARNING,
                    ...     asset_name="test_asset"
                    ... )
                    >>> payload = dest._build_payload(alert)
                    >>> "attachments" in payload
                    True
                    >>> payload["attachments"][0]["color"]
                    '#ff9900'

        """
        # Color based on severity
        severity_colors = {
            AlertSeverity.INFO: "#36a64f",  # Green
            AlertSeverity.WARNING: "#ff9900",  # Orange
            AlertSeverity.ERROR: "#ff3333",  # Red
            AlertSeverity.CRITICAL: "#cc0000",  # Dark red
        }

        color = severity_colors.get(alert.severity, "#999999")

        # Build message blocks
        fields: list[dict[str, object]] = [
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

        if alert.error_message:
            fields.append(
                {
                    "title": "Error",
                    "value": f"```{alert.error_message[:500]}```",
                    "short": False,
                }
            )

        # Build attachment
        attachment: dict[str, object] = {
            "color": color,
            "title": alert.title,
            "text": alert.message,
            "fields": fields,
        }

        payload = {
            "attachments": [attachment],
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload
