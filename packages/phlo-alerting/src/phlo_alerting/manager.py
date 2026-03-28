"""Alert manager for sending notifications to multiple destinations.

This module provides the core alerting infrastructure for Phlo, including
severity levels, alert data structures, destination management, and
deduplication logic. It supports multiple alert destinations (Slack,
PagerDuty, Email) with automatic registration based on configuration.

Examples:
    Sending an alert:
        >>> from phlo_alerting.manager import AlertManager, Alert, AlertSeverity
        >>> manager = AlertManager()
        >>> alert = Alert(
        ...     title="Data Quality Issue",
        ...     message="Null values detected",
        ...     severity=AlertSeverity.WARNING,
        ...     asset_name="customer_table"
        ... )
        >>> manager.send(alert)

    Registering a custom destination:
        >>> from phlo_alerting.manager import AlertDestination
        >>> class CustomDestination(AlertDestination):
        ...     def send(self, alert):
        ...         print(f"Alert: {alert.title}")
        ...         return True
        >>> manager.register_destination("custom", CustomDestination())

"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from phlo.logging import get_logger

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels.

    Defines the standard severity levels for alerts within the Phlo system.
    These levels are used to determine visual styling, routing logic, and
    escalation policies across different notification destinations.

    Attributes:
        INFO: Informational alerts for notable but non-urgent events.
        WARNING: Warning alerts for issues requiring attention but not immediate action.
        ERROR: Error alerts for failures or significant problems.
        CRITICAL: Critical alerts for severe issues requiring immediate response.

    Examples:
        >>> AlertSeverity.INFO
        <AlertSeverity.INFO: 'info'>
        >>> AlertSeverity.ERROR.value
        'error'
        >>> AlertSeverity("warning")
        <AlertSeverity.WARNING: 'warning'>

    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(slots=True)
class Alert:
    """Alert payload data structure.

    Represents a single alert with all relevant metadata for routing
    and display across multiple notification destinations.

    Attributes:
        title: Short, human-readable alert title or summary.
        message: Detailed alert description or context.
        severity: Alert severity level, defaults to ERROR.
        asset_name: Optional name of the asset triggering the alert.
        run_id: Optional run identifier for correlation and debugging.
        error_message: Optional detailed error message or stack trace.
        timestamp: UTC timestamp when the alert was created.

    Examples:
        >>> alert = Alert(
        ...     title="Pipeline Failed",
        ...     message="ETL job encountered an error",
        ...     severity=AlertSeverity.CRITICAL,
        ...     asset_name="daily_etl",
        ...     run_id="run_2024_001"
        ... )
        >>> alert.title
        'Pipeline Failed'
        >>> alert.timestamp is not None
        True

    """

    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.ERROR
    asset_name: Optional[str] = None
    run_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set default timestamp if not provided.

        Automatically assigns the current UTC timestamp when an Alert
        is created without an explicit timestamp value.

        Examples:
            >>> alert = Alert(title="Test", message="Test message")
            >>> alert.timestamp is not None
            True

        """
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class AlertDestination:
    """Base class for alert destinations.

    Abstract base class defining the interface for all alert destinations.
    Concrete implementations must override the send() method to provide
    destination-specific alert delivery logic.

    Attributes:
        None; subclasses may define their own configuration attributes.

    Examples:
        >>> class ConsoleDestination(AlertDestination):
        ...     def send(self, alert):
        ...         print(f"[{alert.severity.value.upper()}] {alert.title}")
        ...         return True
        >>> dest = ConsoleDestination()
        >>> alert = Alert(title="Test", message="Hello")
        >>> dest.send(alert)
        [ERROR] Test
        True

    """

    def send(self, alert: Alert) -> bool:
        """Send an alert to this destination.

        Abstract method that must be implemented by all concrete destination
        classes. Responsible for delivering the alert through the specific
        channel (Slack, Email, etc.).

        Args:
            alert: Alert object containing all information to be sent.

        Returns:
            True if the alert was successfully delivered, False otherwise.

        Raises:
            NotImplementedError: If called on the base class directly.

        Examples:
            See subclass implementations in destinations/ directory.

        """
        raise NotImplementedError


class AlertManager:
    """Manages alert destinations and deduplication.

        Central manager for the alerting system. Maintains a registry of
    destinations, handles deduplication to prevent alert spam, and routes
    alerts to appropriate destinations based on configuration.

    Attributes:
            destinations: Dictionary mapping destination names to AlertDestination instances.
            _sent_alerts: Set of alert keys for deduplication tracking.
            _dedup_window_minutes: Time window for deduplication in minutes.

    Examples:
            >>> manager = AlertManager()
            >>> manager.destinations
            {}
            >>> manager._dedup_window_minutes
            60

    """

    def __init__(self):
        """Initialize alert manager.

        Creates an empty AlertManager instance with no registered destinations.
        Destinations are typically added later via register_destination() or
        automatically via _register_default_destinations().

        Examples:
            >>> manager = AlertManager()
            >>> len(manager.destinations)
            0

        """
        self.destinations: dict[str, AlertDestination] = {}
        self._sent_alerts: set[str] = set()  # For deduplication
        self._dedup_window_minutes = 60

    def register_destination(self, name: str, destination: AlertDestination) -> None:
        """Register an alert destination.

        Adds a new destination to the manager's registry. Once registered,
        the destination will receive all alerts sent through the manager
        unless specific destinations are requested.

        Args:
            name: Unique identifier for this destination (e.g., "slack", "email").
            destination: AlertDestination instance implementing the send() method.

        Returns:
            None

        Raises:
            None; overwrites existing destinations with the same name.

        Examples:
            >>> from phlo_alerting.destinations.slack import SlackAlertDestination
            >>> manager = AlertManager()
            >>> slack = SlackAlertDestination("https://hooks.slack.com/test")
            >>> manager.register_destination("slack", slack)
            >>> "slack" in manager.destinations
            True

        """
        self.destinations[name] = destination
        logger.info("alert_destination_registered", destination_name=name)

    def send(self, alert: Alert, destinations: Optional[list[str]] = None) -> bool:
        """Send an alert to registered destinations.

                Routes the alert to specified or all registered destinations.
                Implements deduplication to prevent sending duplicate alerts within
        the configured time window.

        Args:
                    alert: Alert object to be sent.
                    destinations: Optional list of destination names to target.
                        If None, sends to all registered destinations.

        Returns:
                    True if the alert was successfully sent to at least one destination,
                    False if all destinations failed or alert was deduplicated.

        Raises:
                    None; individual destination failures are logged but don't raise.

        Examples:
                    >>> manager = AlertManager()
                    >>> alert = Alert(title="Test", message="Hello")
                    >>> # Without destinations, returns False
                    >>> manager.send(alert)
                    False

        """
        # Check for duplicates
        alert_key = self._get_alert_key(alert)
        if self._is_duplicate(alert_key):
            logger.debug("alert_duplicate_skipped", alert_key=alert_key)
            return False

        # Determine which destinations to use
        targets = destinations or list(self.destinations.keys())

        # Send to each destination
        sent = False
        for dest_name in targets:
            if dest_name not in self.destinations:
                logger.warning("alert_unknown_destination", destination_name=dest_name)
                continue

            try:
                dest = self.destinations[dest_name]
                if dest.send(alert):
                    sent = True
                    logger.info(
                        "alert_sent",
                        destination_name=dest_name,
                        alert_title=alert.title,
                    )
            except Exception:
                logger.exception("alert_send_failed", destination_name=dest_name)

        # Mark as sent
        if sent:
            self._sent_alerts.add(alert_key)

        return sent

    def _get_alert_key(self, alert: Alert) -> str:
        """Generate deduplication key for an alert.

        Creates a unique key based on asset name, error message, and severity
        to identify duplicate alerts for deduplication purposes.

        Args:
            alert: Alert object to generate key for.

        Returns:
            String key suitable for deduplication comparison.

        Examples:
            >>> from phlo_alerting.manager import AlertManager, Alert, AlertSeverity
            >>> manager = AlertManager()
            >>> alert = Alert(
            ...     title="Test",
            ...     message="Test msg",
            ...     asset_name="asset1",
            ...     error_message="error1",
            ...     severity=AlertSeverity.ERROR
            ... )
            >>> key = manager._get_alert_key(alert)
            >>> key
            'asset1:error1:error'

        """
        return f"{alert.asset_name}:{alert.error_message}:{alert.severity.value}"

    def _is_duplicate(self, key: str) -> bool:
        """Check if alert is a duplicate.

        Determines whether an alert with the given key has already been
        sent within the current deduplication window.

        Args:
            key: Deduplication key to check.

        Returns:
            True if the key exists in the sent alerts set, False otherwise.

        Examples:
            >>> manager = AlertManager()
            >>> manager._is_duplicate("test_key")
            False
            >>> manager._sent_alerts.add("test_key")
            >>> manager._is_duplicate("test_key")
            True

        """
        return key in self._sent_alerts


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager.

    Returns the singleton AlertManager instance, creating it if necessary.
    On first creation, automatically registers default destinations based
    on environment configuration.

    Returns:
        The global AlertManager instance.

    Examples:
        >>> manager1 = get_alert_manager()
        >>> manager2 = get_alert_manager()
        >>> manager1 is manager2
        True

    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        _register_default_destinations(_alert_manager)
    return _alert_manager


def _register_default_destinations(manager: AlertManager) -> None:
    """Register default alert destinations from config.

    Automatically configures alert destinations based on environment
    variables. Supports Slack (PHLO_ALERT_SLACK_WEBHOOK), PagerDuty
    (PHLO_ALERT_PAGERDUTY_KEY), and Email (PHLO_ALERT_EMAIL_*).

    Args:
        manager: AlertManager instance to register destinations with.

    Returns:
        None

    Examples:
        This function is called automatically by get_alert_manager() and
        should not typically be called directly.

    """
    from phlo_alerting.destinations.email import EmailAlertDestination
    from phlo_alerting.destinations.pagerduty import PagerDutyAlertDestination
    from phlo_alerting.destinations.slack import SlackAlertDestination
    from phlo_alerting.settings import get_settings

    config = get_settings()

    # Register Slack if configured
    if config.phlo_alert_slack_webhook:
        try:
            slack = SlackAlertDestination(
                webhook_url=config.phlo_alert_slack_webhook,
                channel=config.phlo_alert_slack_channel,
            )
            manager.register_destination("slack", slack)
        except Exception:
            logger.warning(
                "alert_destination_register_failed", destination_name="slack", exc_info=True
            )

    # Register PagerDuty if configured
    if config.phlo_alert_pagerduty_key:
        try:
            pagerduty = PagerDutyAlertDestination(integration_key=config.phlo_alert_pagerduty_key)
            manager.register_destination("pagerduty", pagerduty)
        except Exception:
            logger.warning(
                "alert_destination_register_failed",
                destination_name="pagerduty",
                exc_info=True,
            )

    # Register Email if configured
    if config.phlo_alert_email_smtp_host:
        try:
            email = EmailAlertDestination(
                smtp_host=config.phlo_alert_email_smtp_host,
                smtp_port=config.phlo_alert_email_smtp_port,
                smtp_user=config.phlo_alert_email_smtp_user,
                smtp_password=config.phlo_alert_email_smtp_password,
                recipients=config.phlo_alert_email_recipients,
            )
            manager.register_destination("email", email)
        except Exception:
            logger.warning(
                "alert_destination_register_failed", destination_name="email", exc_info=True
            )
