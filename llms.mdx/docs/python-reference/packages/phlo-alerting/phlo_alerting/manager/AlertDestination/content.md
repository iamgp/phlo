# AlertDestination (/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/AlertDestination)



Base class for alert destinations.

Abstract base class defining the interface for all alert destinations.
Concrete implementations must override the send() method to provide
destination-specific alert delivery logic.

Functions [#functions]

<PyFunction name="&#x22;send&#x22;" type="&#x22;(self, alert) -> bool&#x22;">
  Send an alert to this destination.

  Abstract method that must be implemented by all concrete destination
  classes. Responsible for delivering the alert through the specific
  channel (Slack, Email, etc.).

  <PySourceCode>
    ```python
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
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;alert&#x22;" type="&#x22;Alert&#x22;" value="undefined">
      Alert object containing all information to be sent.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if the alert was successfully delivered, False otherwise.
  </PyFunctionReturn>
</PyFunction>
