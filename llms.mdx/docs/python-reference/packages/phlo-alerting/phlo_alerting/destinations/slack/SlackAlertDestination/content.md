# SlackAlertDestination (/docs/python-reference/packages/phlo-alerting/phlo_alerting/destinations/slack/SlackAlertDestination)



Send alerts to Slack via webhook.

Concrete implementation of AlertDestination that delivers alerts
to Slack channels using incoming webhooks. Formats messages as Slack
attachments with severity-based colors and structured field layouts.

Attributes [#attributes]

<PyAttribute name="&#x22;webhook_url&#x22;" type="null" value="&#x22;webhook_url&#x22;">
  Slack incoming webhook URL for posting messages.
</PyAttribute>

<PyAttribute name="&#x22;channel&#x22;" type="null" value="&#x22;channel&#x22;">
  Optional channel override (e.g., "#alerts").
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, webhook_url, channel=None)&#x22;">
  Initialize Slack destination.

  Creates a SlackAlertDestination instance configured to send
  messages to the specified webhook URL. The webhook URL must be a
  valid Slack incoming webhook.

  default channel (e.g., "#alerts", "@username").

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;webhook_url&#x22;" type="&#x22;str&#x22;" value="undefined">
      Slack incoming webhook URL obtained from
      the Slack app configuration (e.g., "[https://hooks.slack.com/services/](https://hooks.slack.com/services/)...").
    </PyParameter>

    <PyParameter name="&#x22;channel&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional channel name to override the webhook's
    </PyParameter>
  </div>

  <PyFunctionReturn type="null">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;send&#x22;" type="&#x22;(self, alert) -> bool&#x22;">
  Send alert to Slack.

  Posts the alert to the configured Slack webhook as a message
  attachment with severity-based coloring and structured fields.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object containing notification details.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the message was posted successfully (HTTP 200),
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_payload&#x22;" type="&#x22;(self, alert) -> dict&#x22;">
  Build Slack message payload.

  Constructs a Slack message attachment payload with severity-based
  color coding and structured field layout. Includes asset name, run ID,
  and error details when available.

  <PySourceCode>
    ````python
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
                    "value": f"\```{alert.error_message[:500]}\```",
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
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object to format.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary representing Slack message payload.
  </PyFunctionReturn>
</PyFunction>
