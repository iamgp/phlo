# AlertManager (/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/AlertManager)



Manages alert destinations and deduplication.

Central manager for the alerting system. Maintains a registry of
destinations, handles deduplication to prevent alert spam, and routes
alerts to appropriate destinations based on configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;destinations&#x22;" type="&#x22;dict[str, AlertDestination]&#x22;" value="&#x22;{}&#x22;">
  Dictionary mapping destination names to AlertDestination instances.
</PyAttribute>

<PyAttribute name="&#x22;_sent_alerts&#x22;" type="&#x22;set[str]&#x22;" value="&#x22;set()&#x22;">
  Set of alert keys for deduplication tracking.
</PyAttribute>

<PyAttribute name="&#x22;_dedup_window_minutes&#x22;" type="null" value="&#x22;60&#x22;">
  Time window for deduplication in minutes.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self)&#x22;">
  Initialize alert manager.

  Creates an empty AlertManager instance with no registered destinations.
  Destinations are typically added later via register\_destination() or
  automatically via \_register\_default\_destinations().

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;register_destination&#x22;" type="&#x22;(self, name, destination) -> None&#x22;">
  Register an alert destination.

  Adds a new destination to the manager's registry. Once registered,
  the destination will receive all alerts sent through the manager
  unless specific destinations are requested.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Unique identifier for this destination (e.g., "slack", "email").
    </PyParameter>

    <PyParameter name="&#x22;destination&#x22;" type="&#x22;AlertDestination&#x22;" value="undefined">
      AlertDestination instance implementing the send() method.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;send&#x22;" type="&#x22;(self, alert, destinations=None) -> bool&#x22;">
  Send an alert to registered destinations.

  Routes the alert to specified or all registered destinations.
  Implements deduplication to prevent sending duplicate alerts within
  the configured time window.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object to be sent.
    </PyParameter>

    <PyParameter name="&#x22;destinations&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;">
      Optional list of destination names to target.
      If None, sends to all registered destinations.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the alert was successfully sent to at least one destination,
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_alert_key&#x22;" type="&#x22;(self, alert) -> str&#x22;">
  Generate deduplication key for an alert.

  Creates a unique key based on asset name, error message, and severity
  to identify duplicate alerts for deduplication purposes.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object to generate key for.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    String key suitable for deduplication comparison.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_is_duplicate&#x22;" type="&#x22;(self, key) -> bool&#x22;">
  Check if alert is a duplicate.

  Determines whether an alert with the given key has already been
  sent within the current deduplication window.

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
      Deduplication key to check.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the key exists in the sent alerts set, False otherwise.
  </PyFunctionReturn>
</PyFunction>
