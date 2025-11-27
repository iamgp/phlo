"""
Consumer notification system for contract changes and SLA violations.

Handles sending notifications to data consumers about schema changes
and SLA breaches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol


class NotificationType(str, Enum):
    """Types of contract notifications."""

    SCHEMA_CHANGE_PROPOSED = "schema_change_proposed"
    SCHEMA_CHANGE_MERGED = "schema_change_merged"
    SLA_BREACH = "sla_breach"
    QUALITY_VIOLATION = "quality_violation"
    FRESHNESS_VIOLATION = "freshness_violation"


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


@dataclass
class NotificationConfig:
    """Configuration for notifications."""

    enabled: bool = True
    channels: list[NotificationChannel] = field(default_factory=list)
    on_events: list[NotificationType] = field(default_factory=list)
    slack_webhook: Optional[str] = None
    email_recipients: list[str] = field(default_factory=list)
    pagerduty_key: Optional[str] = None


@dataclass
class ContractNotification:
    """Notification about a contract event."""

    type: NotificationType
    contract_name: str
    subject: str
    message: str
    details: dict = field(default_factory=dict)
    severity: str = "info"  # info, warning, critical
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recipients: list[str] = field(default_factory=list)


class NotificationDestination(Protocol):
    """Protocol for notification destinations."""

    def send(self, notification: ContractNotification) -> bool:
        """Send a notification."""
        ...


class SlackNotificationDestination:
    """Send notifications to Slack."""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        """Initialize with webhook URL."""
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, notification: ContractNotification) -> bool:
        """Send notification to Slack."""
        try:
            import requests

            # Build Slack message
            color_map = {"info": "#36a64f", "warning": "#ff9900", "critical": "#ff0000"}
            color = color_map.get(notification.severity, "#36a64f")

            payload = {
                "channel": self.channel,
                "attachments": [
                    {
                        "color": color,
                        "title": notification.subject,
                        "text": notification.message,
                        "fields": [
                            {
                                "title": "Contract",
                                "value": notification.contract_name,
                                "short": True,
                            },
                            {
                                "title": "Type",
                                "value": notification.type.value,
                                "short": True,
                            },
                            {
                                "title": "Timestamp",
                                "value": notification.timestamp.isoformat(),
                                "short": True,
                            },
                        ],
                    }
                ],
            }

            # Add detail fields if present
            if notification.details:
                for key, value in list(notification.details.items())[:5]:
                    payload["attachments"][0]["fields"].append(
                        {"title": key, "value": str(value), "short": False}
                    )

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False


class EmailNotificationDestination:
    """Send notifications via email."""

    def __init__(self, smtp_host: str, smtp_port: int, from_address: str):
        """Initialize email destination."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_address = from_address

    def send(self, notification: ContractNotification) -> bool:
        """Send notification via email."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            if not notification.recipients:
                return False

            # Build HTML email
            html = f"""
            <html>
                <body>
                    <h2>{notification.subject}</h2>
                    <p>{notification.message}</p>
                    <hr>
                    <p><strong>Contract:</strong> {notification.contract_name}</p>
                    <p><strong>Type:</strong> {notification.type.value}</p>
                    <p><strong>Severity:</strong> {notification.severity.upper()}</p>
                    <p><strong>Time:</strong> {notification.timestamp.isoformat()}</p>
            """

            if notification.details:
                html += "<h3>Details:</h3><ul>"
                for key, value in notification.details.items():
                    html += f"<li><strong>{key}:</strong> {value}</li>"
                html += "</ul>"

            html += "</body></html>"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.subject
            msg["From"] = self.from_address
            msg["To"] = ", ".join(notification.recipients)

            part = MIMEText(html, "html")
            msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.sendmail(
                    self.from_address, notification.recipients, msg.as_string()
                )

            return True

        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False


class NotificationManager:
    """
    Manages notifications to consumers.

    Routes notifications to configured channels.
    """

    def __init__(self):
        """Initialize notification manager."""
        self.destinations: dict[NotificationChannel, NotificationDestination] = {}
        self.notification_history: list[ContractNotification] = []

    def register_destination(
        self, channel: NotificationChannel, destination: NotificationDestination
    ) -> None:
        """Register a notification destination."""
        self.destinations[channel] = destination

    def notify(self, notification: ContractNotification, channels: list[NotificationChannel] = None) -> bool:
        """
        Send notification through configured channels.

        Args:
            notification: Notification to send
            channels: Specific channels to use (if None, uses all registered)

        Returns:
            True if at least one channel succeeded
        """
        if channels is None:
            channels = list(self.destinations.keys())

        success = False
        for channel in channels:
            if channel in self.destinations:
                try:
                    if self.destinations[channel].send(notification):
                        success = True
                except Exception as e:
                    print(f"Error sending via {channel}: {e}")

        # Record in history
        self.notification_history.append(notification)

        return success

    def get_notification_history(
        self,
        contract_name: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
    ) -> list[ContractNotification]:
        """Get notification history with optional filtering."""
        results = self.notification_history

        if contract_name:
            results = [n for n in results if n.contract_name == contract_name]

        if notification_type:
            results = [n for n in results if n.type == notification_type]

        return results[-limit:]
