# manager (/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager)



Alert manager for sending notifications to multiple destinations.

This module provides the core alerting infrastructure for Phlo, including
severity levels, alert data structures, destination management, and
deduplication logic. It supports multiple alert destinations (Slack,
PagerDuty, Email) with automatic registration based on configuration.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;AlertSeverity&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/AlertSeverity&#x22;" />

      <Card title="&#x22;Alert&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/Alert&#x22;" />

      <Card title="&#x22;AlertDestination&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/AlertDestination&#x22;" />

      <Card title="&#x22;AlertManager&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/AlertManager&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_alert_manager&#x22;" type="&#x22;() -> AlertManager&#x22;">
      Get or create global alert manager.

      Returns the singleton AlertManager instance, creating it if necessary.
      On first creation, automatically registers default destinations based
      on environment configuration.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_alerting.manager.AlertManager&#x22;">
        The global AlertManager instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_register_default_destinations&#x22;" type="&#x22;(manager) -> None&#x22;">
      Register default alert destinations from config.

      Automatically configures alert destinations based on environment
      variables. Supports Slack (PHLO\_ALERT\_SLACK\_WEBHOOK), PagerDuty
      (PHLO\_ALERT\_PAGERDUTY\_KEY), and Email (PHLO\_ALERT\_EMAIL\_\*).

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manager&#x22;" type="&#x22;AlertManager&#x22;" value="undefined">
          AlertManager instance to register destinations with.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
