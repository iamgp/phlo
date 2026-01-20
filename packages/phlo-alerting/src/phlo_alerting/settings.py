"""Alerting settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class AlertingSettings(BaseConfig):
    """Alert integration configuration (Slack, PagerDuty, Email)."""

    phlo_alert_slack_webhook: str | None = Field(
        default=None, description="Slack incoming webhook URL"
    )
    phlo_alert_slack_channel: str | None = Field(
        default=None, description="Default Slack channel for alerts"
    )
    phlo_alert_pagerduty_key: str | None = Field(
        default=None, description="PagerDuty Events API v2 integration key"
    )
    phlo_alert_email_smtp_host: str | None = Field(default=None, description="SMTP server hostname")
    phlo_alert_email_smtp_port: int = Field(default=587, description="SMTP server port")
    phlo_alert_email_smtp_user: str | None = Field(default=None, description="SMTP username")
    phlo_alert_email_smtp_password: str | None = Field(default=None, description="SMTP password")
    phlo_alert_email_recipients: list[str] = Field(
        default_factory=list, description="Email recipients for alerts"
    )


@lru_cache(maxsize=1)
def get_settings() -> AlertingSettings:
    return AlertingSettings()
