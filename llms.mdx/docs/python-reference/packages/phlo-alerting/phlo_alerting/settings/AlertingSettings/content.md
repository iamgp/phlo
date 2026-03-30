# AlertingSettings (/docs/python-reference/packages/phlo-alerting/phlo_alerting/settings/AlertingSettings)



Alert integration configuration for Slack, PagerDuty, and Email.

Pydantic-based configuration class that automatically loads settings
from environment variables with "PHLO\_ALERT\_" prefix. Provides
type-safe access to alerting configuration with validation.

Attributes [#attributes]

<PyAttribute name="&#x22;phlo_alert_slack_webhook&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Slack incoming webhook URL')&#x22;">
  Slack incoming webhook URL for posting alerts.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_slack_channel&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Default Slack channel for alerts')&#x22;">
  Optional default channel override (e.g., "#alerts").
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_pagerduty_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='PagerDuty Events API v2 integration key')&#x22;">
  PagerDuty Events API v2 integration key.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_email_smtp_host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='SMTP server hostname')&#x22;">
  SMTP server hostname for email alerts.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_email_smtp_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=587, description='SMTP server port')&#x22;">
  SMTP server port, defaults to 587.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_email_smtp_user&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='SMTP username')&#x22;">
  SMTP authentication username.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_email_smtp_password&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='SMTP password')&#x22;">
  SMTP authentication password.
</PyAttribute>

<PyAttribute name="&#x22;phlo_alert_email_recipients&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;Field(default_factory=list, description='Email recipients for alerts')&#x22;">
  List of email addresses to receive alerts.
</PyAttribute>
