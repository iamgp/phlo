"""Alert manager for sending notifications to multiple destinations."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert payload."""

    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.ERROR
    asset_name: Optional[str] = None
    run_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set default timestamp."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class AlertDestination:
    """Base class for alert destinations."""

    def send(self, alert: Alert) -> bool:
        """
        Send an alert.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully, False otherwise
        """
        raise NotImplementedError


class AlertManager:
    """Manages alert destinations and deduplication."""

    def __init__(self):
        """Initialize alert manager."""
        self.destinations: dict[str, AlertDestination] = {}
        self._sent_alerts: set[str] = set()  # For deduplication
        self._dedup_window_minutes = 60

    def register_destination(self, name: str, destination: AlertDestination) -> None:
        """
        Register an alert destination.

        Args:
            name: Name of the destination
            destination: AlertDestination instance
        """
        self.destinations[name] = destination
        logger.info(f"Registered alert destination: {name}")

    def send(self, alert: Alert, destinations: Optional[list[str]] = None) -> bool:
        """
        Send an alert to registered destinations.

        Args:
            alert: Alert to send
            destinations: Specific destinations to use (None = all)

        Returns:
            True if sent to at least one destination successfully
        """
        # Check for duplicates
        alert_key = self._get_alert_key(alert)
        if self._is_duplicate(alert_key):
            logger.debug(f"Skipping duplicate alert: {alert_key}")
            return False

        # Determine which destinations to use
        targets = destinations or list(self.destinations.keys())

        # Send to each destination
        sent = False
        for dest_name in targets:
            if dest_name not in self.destinations:
                logger.warning(f"Unknown destination: {dest_name}")
                continue

            try:
                dest = self.destinations[dest_name]
                if dest.send(alert):
                    sent = True
                    logger.info(f"Sent alert to {dest_name}: {alert.title}")
            except Exception as e:
                logger.exception(f"Failed to send alert to {dest_name}: {e}")

        # Mark as sent
        if sent:
            self._sent_alerts.add(alert_key)

        return sent

    def _get_alert_key(self, alert: Alert) -> str:
        """Generate deduplication key for an alert."""
        return f"{alert.asset_name}:{alert.error_message}:{alert.severity.value}"

    def _is_duplicate(self, key: str) -> bool:
        """Check if alert is a duplicate."""
        return key in self._sent_alerts


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        _register_default_destinations(_alert_manager)
    return _alert_manager


def _register_default_destinations(manager: AlertManager) -> None:
    """Register default alert destinations from config."""
    from phlo_alerting.destinations.email import EmailAlertDestination
    from phlo_alerting.destinations.pagerduty import PagerDutyAlertDestination
    from phlo_alerting.destinations.slack import SlackAlertDestination
    from phlo.config import get_settings

    config = get_settings()

    # Register Slack if configured
    if hasattr(config, "phlo_alert_slack_webhook") and config.phlo_alert_slack_webhook:
        try:
            slack = SlackAlertDestination(
                webhook_url=config.phlo_alert_slack_webhook,
                channel=getattr(config, "phlo_alert_slack_channel", None),
            )
            manager.register_destination("slack", slack)
        except Exception as e:
            logger.warning(f"Failed to register Slack destination: {e}")

    # Register PagerDuty if configured
    if hasattr(config, "phlo_alert_pagerduty_key") and config.phlo_alert_pagerduty_key:
        try:
            pagerduty = PagerDutyAlertDestination(integration_key=config.phlo_alert_pagerduty_key)
            manager.register_destination("pagerduty", pagerduty)
        except Exception as e:
            logger.warning(f"Failed to register PagerDuty destination: {e}")

    # Register Email if configured
    if hasattr(config, "phlo_alert_email_smtp_host") and config.phlo_alert_email_smtp_host:
        try:
            email = EmailAlertDestination(
                smtp_host=config.phlo_alert_email_smtp_host,
                smtp_port=getattr(config, "phlo_alert_email_smtp_port", 587),
                smtp_user=getattr(config, "phlo_alert_email_smtp_user", None),
                smtp_password=getattr(config, "phlo_alert_email_smtp_password", None),
                recipients=getattr(config, "phlo_alert_email_recipients", []),
            )
            manager.register_destination("email", email)
        except Exception as e:
            logger.warning(f"Failed to register Email destination: {e}")
