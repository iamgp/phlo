"""Email alert destination."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from phlo.logging import get_logger
from phlo_alerting.manager import Alert, AlertDestination, AlertSeverity

logger = get_logger(__name__)


class EmailAlertDestination(AlertDestination):
    """Send alerts via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        recipients: Optional[list[str]] = None,
    ):
        """
        Initialize email destination.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (default: 587)
            smtp_user: SMTP username (optional)
            smtp_password: SMTP password (optional)
            recipients: List of email addresses to send to
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.recipients = recipients or []

    def send(self, alert: Alert) -> bool:
        """Send alert via email."""
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

        except Exception as e:
            logger.exception(f"Failed to send email alert: {e}")
            return False

    def _build_text(self, alert: Alert) -> str:
        """Build plain text email content."""
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

    def _build_html(self, alert: Alert) -> str:
        """Build HTML email content."""
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
