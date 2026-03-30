# EmailAlertDestination (/docs/python-reference/packages/phlo-alerting/phlo_alerting/destinations/email/EmailAlertDestination)



Send alerts via email using SMTP.

Concrete implementation of AlertDestination that delivers alerts
to email recipients via SMTP. Supports TLS encryption and
authentication. Formats alerts as both plain text and HTML with
severity-based color coding.

Attributes [#attributes]

<PyAttribute name="&#x22;smtp_host&#x22;" type="null" value="&#x22;smtp_host&#x22;">
  SMTP server hostname.
</PyAttribute>

<PyAttribute name="&#x22;smtp_port&#x22;" type="null" value="&#x22;smtp_port&#x22;">
  SMTP server port number.
</PyAttribute>

<PyAttribute name="&#x22;smtp_user&#x22;" type="null" value="&#x22;smtp_user&#x22;">
  SMTP authentication username (optional).
</PyAttribute>

<PyAttribute name="&#x22;smtp_password&#x22;" type="null" value="&#x22;smtp_password&#x22;">
  SMTP authentication password (optional).
</PyAttribute>

<PyAttribute name="&#x22;recipients&#x22;" type="null" value="&#x22;recipients or []&#x22;">
  List of email addresses to receive alerts.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, smtp_host, smtp_port=587, smtp_user=None, smtp_password=None, recipients=None)&#x22;">
  Initialize email destination.

  Creates an EmailAlertDestination instance with SMTP configuration.
  The destination is ready to send alerts once initialized, though
  actual SMTP connections are established per-send.

  <PySourceCode>
    ```python
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        recipients: Optional[list[str]] = None,
    ):
        """Initialize email destination.

        Creates an EmailAlertDestination instance with SMTP configuration.
        The destination is ready to send alerts once initialized, though
        actual SMTP connections are established per-send.

        Args:
            smtp_host: SMTP server hostname (e.g., "smtp.gmail.com").
            smtp_port: SMTP server port, defaults to 587 for TLS.
            smtp_user: SMTP username for authentication (optional).
            smtp_password: SMTP password for authentication (optional).
            recipients: List of email addresses to send alerts to.

        Returns:
            None

        Raises:
            None; validation occurs during send().

        Examples:
            >>> dest = EmailAlertDestination(
            ...     smtp_host="smtp.example.com",
            ...     smtp_port=587,
            ...     smtp_user="alerts@example.com",
            ...     recipients=["team@example.com"]
            ... )

        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.recipients = recipients or []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;smtp_host&#x22;" type="&#x22;str&#x22;" value="undefined">
      SMTP server hostname (e.g., "smtp.gmail.com").
    </PyParameter>

    <PyParameter name="&#x22;smtp_port&#x22;" type="&#x22;int&#x22;" value="&#x22;587&#x22;">
      SMTP server port, defaults to 587 for TLS.
    </PyParameter>

    <PyParameter name="&#x22;smtp_user&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      SMTP username for authentication (optional).
    </PyParameter>

    <PyParameter name="&#x22;smtp_password&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      SMTP password for authentication (optional).
    </PyParameter>

    <PyParameter name="&#x22;recipients&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;">
      List of email addresses to send alerts to.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;send&#x22;" type="&#x22;(self, alert) -> bool&#x22;">
  Send alert via email.

  Connects to the SMTP server, authenticates if credentials are
  provided, and sends the alert as a multipart email (plain text + HTML).
  Uses TLS encryption via STARTTLS.

  <PySourceCode>
    ```python
    def send(self, alert: Alert) -> bool:
        """Send alert via email.

                Connects to the SMTP server, authenticates if credentials are
        provided, and sends the alert as a multipart email (plain text + HTML).
        Uses TLS encryption via STARTTLS.

        Args:
                    alert: Alert object containing notification details.

        Returns:
                    True if email was sent successfully, False otherwise.

        Raises:
                    None; SMTP errors are caught and logged.

        Examples:
                    >>> from phlo_alerting.manager import Alert, AlertSeverity
                    >>> alert = Alert(
                    ...     title="Test Alert",
                    ...     message="Test message",
                    ...     severity=AlertSeverity.WARNING
                    ... )
                    >>> result = dest.send(alert)
                    >>> isinstance(result, bool)
                    True

        """
        if not self.recipients:
            logger.warning("No email recipients configured")
            return False

        try:
            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg["From"] = self.smtp_user or "phlo@example.com"
            msg["To"] = ", ".join(self.recipients)

            # Build plain text and HTML versions
            text_content = self._build_text(alert)
            html_content = self._build_html(alert)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(msg["From"], self.recipients, msg.as_string())

            return True

        except Exception:
            logger.exception(
                "email_alert_send_failed",
                alert_title=alert.title,
                severity=alert.severity.value,
                asset_name=alert.asset_name,
                run_id=alert.run_id,
                recipient_count=len(self.recipients),
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
    True if email was sent successfully, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_text&#x22;" type="&#x22;(self, alert) -> str&#x22;">
  Build plain text email content.

  Constructs a human-readable plain text representation of the alert
  suitable for email clients that don't support HTML.

  <PySourceCode>
    ```python
        def _build_text(self, alert: Alert) -> str:
            """Build plain text email content.

            Constructs a human-readable plain text representation of the alert
            suitable for email clients that don't support HTML.

            Args:
                alert: Alert object to format.

            Returns:
                Plain text email content as a string.

            Examples:
                >>> from phlo_alerting.manager import Alert, AlertSeverity
                >>> alert = Alert(
                ...     title="Test",
                ...     message="Test message",
                ...     severity=AlertSeverity.ERROR,
                ...     asset_name="test_asset"
                ... )
                >>> text = dest._build_text(alert)
                >>> "Phlo Alert Notification" in text
                True
                >>> "Asset: test_asset" in text
                True

            """
            content = f"""
    Phlo Alert Notification
    =======================

    Title: {alert.title}
    Severity: {alert.severity.value.upper()}
    Time: {alert.timestamp.isoformat() if alert.timestamp else "N/A"}

    Message:
    {alert.message}
    """

            if alert.asset_name:
                content += f"\nAsset: {alert.asset_name}"

            if alert.run_id:
                content += f"\nRun ID: {alert.run_id}"

            if alert.error_message:
                content += f"\n\nError Details:\n{alert.error_message}"

            return content
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object to format.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Plain text email content as a string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_html&#x22;" type="&#x22;(self, alert) -> str&#x22;">
  Build HTML email content.

  Constructs an HTML representation of the alert with severity-based
  color coding and structured layout. Uses inline styles for email client
  compatibility.

  <PySourceCode>
    ```python
    def _build_html(self, alert: Alert) -> str:
        """Build HTML email content.

                Constructs an HTML representation of the alert with severity-based
        color coding and structured layout. Uses inline styles for email client
        compatibility.

        Args:
                    alert: Alert object to format.

        Returns:
                    HTML email content as a string.

        Examples:
                    >>> from phlo_alerting.manager import Alert, AlertSeverity
                    >>> alert = Alert(title="Test", message="Test", severity=AlertSeverity.CRITICAL)
                    >>> html = dest._build_html(alert)
                    >>> "<html>" in html
                    True
                    >>> "#cc0000" in html  # Critical severity color
                    True

        """
        severity_color = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.ERROR: "#ff3333",
            AlertSeverity.CRITICAL: "#cc0000",
        }.get(alert.severity, "#999999")

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="border-left: 4px solid {severity_color}; padding: 15px; background: #f9f9f9; margin: 10px 0;">
                    <h2 style="margin-top: 0; color: {severity_color};">{alert.title}</h2>

                    <table style="width: 100%; margin: 15px 0;">
                        <tr>
                            <td style="font-weight: bold; width: 120px;">Severity:</td>
                            <td style="color: {severity_color}; font-weight: bold;">{alert.severity.value.upper()}</td>
                        </tr>
                        <tr>
                            <td style="font-weight: bold;">Time:</td>
                            <td>{alert.timestamp.isoformat() if alert.timestamp else "N/A"}</td>
                        </tr>
        """

        if alert.asset_name:
            html += f"""
                        <tr>
                            <td style="font-weight: bold;">Asset:</td>
                            <td>{alert.asset_name}</td>
                        </tr>
            """

        if alert.run_id:
            html += f"""
                        <tr>
                            <td style="font-weight: bold;">Run ID:</td>
                            <td><code>{alert.run_id}</code></td>
                        </tr>
            """

        html += """
                    </table>

                    <div style="margin: 15px 0;">
                        <h3>Message</h3>
                        <p>{}</p>
                    </div>
        """.format(alert.message)

        if alert.error_message:
            html += f"""
                    <div style="background: #f0f0f0; padding: 10px; border-radius: 3px; margin: 15px 0;">
                        <h3>Error Details</h3>
                        <pre style="margin: 0; font-size: 12px;">{alert.error_message}</pre>
                    </div>
            """

        html += """
                </div>
            </body>
        </html>
        """

        return html
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object to format.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    HTML email content as a string.
  </PyFunctionReturn>
</PyFunction>
