from typing import Optional

from pydantic import Field

from phlo.config.base import BaseConfig


class AlertingConfig(BaseConfig):
    """Alert integration configuration (Slack, PagerDuty, Email)."""

    phlo_alert_slack_webhook: Optional[str] = Field(
        default=None, description="Slack incoming webhook URL"
    )
    phlo_alert_slack_channel: Optional[str] = Field(
        default=None, description="Default Slack channel for alerts"
    )
    phlo_alert_pagerduty_key: Optional[str] = Field(
        default=None, description="PagerDuty Events API v2 integration key"
    )
    phlo_alert_email_smtp_host: Optional[str] = Field(
        default=None, description="SMTP server hostname"
    )
    phlo_alert_email_smtp_port: int = Field(default=587, description="SMTP server port")
    phlo_alert_email_smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    phlo_alert_email_smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    phlo_alert_email_recipients: list[str] = Field(
        default_factory=list, description="Email recipients for alerts"
    )
