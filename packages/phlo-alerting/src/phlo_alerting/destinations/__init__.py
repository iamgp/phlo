"""Alert destination implementations.

This package contains concrete implementations of the AlertDestination
base class for various notification channels. Each module provides a
specific destination type with its own configuration and delivery logic.

Available Destinations:
    email: SMTP-based email delivery via EmailAlertDestination.
    slack: Slack webhook integration via SlackAlertDestination.
    pagerduty: PagerDuty Events API via PagerDutyAlertDestination.

Examples:
    Using destinations directly:
        >>> from phlo_alerting.destinations.slack import SlackAlertDestination
        >>> dest = SlackAlertDestination("https://hooks.slack.com/...")
        >>> dest.send(alert)

    The AlertManager automatically instantiates destinations based on
    environment configuration when get_alert_manager() is called.

See Also:
    manager.AlertDestination: Base class for all destinations.
    manager.AlertManager: Central manager that coordinates destinations.

"""
