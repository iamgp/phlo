# Alert (/docs/python-reference/packages/phlo-alerting/phlo_alerting/manager/Alert)



Alert payload data structure.

Represents a single alert with all relevant metadata for routing
and display across multiple notification destinations.

Attributes [#attributes]

<PyAttribute name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="null">
  Short, human-readable alert title or summary.
</PyAttribute>

<PyAttribute name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null">
  Detailed alert description or context.
</PyAttribute>

<PyAttribute name="&#x22;severity&#x22;" type="&#x22;AlertSeverity&#x22;" value="&#x22;AlertSeverity.ERROR&#x22;">
  Alert severity level, defaults to ERROR.
</PyAttribute>

<PyAttribute name="&#x22;asset_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Optional name of the asset triggering the alert.
</PyAttribute>

<PyAttribute name="&#x22;run_id&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Optional run identifier for correlation and debugging.
</PyAttribute>

<PyAttribute name="&#x22;error_message&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
  Optional detailed error message or stack trace.
</PyAttribute>

<PyAttribute name="&#x22;timestamp&#x22;" type="&#x22;Optional[datetime]&#x22;" value="&#x22;None&#x22;">
  UTC timestamp when the alert was created.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__post_init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Set default timestamp if not provided.

  Automatically assigns the current UTC timestamp when an Alert
  is created without an explicit timestamp value.

  <PySourceCode>
    ```python
    def __post_init__(self) -> None:
        """Set default timestamp if not provided.

        Automatically assigns the current UTC timestamp when an Alert
        is created without an explicit timestamp value.

        Examples:
            >>> alert = Alert(title="Test", message="Test message")
            >>> alert.timestamp is not None
            True

        """
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, title, message, severity=AlertSeverity.ERROR, asset_name=None, run_id=None, error_message=None, timestamp=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;severity&#x22;" type="&#x22;AlertSeverity&#x22;" value="&#x22;AlertSeverity.ERROR&#x22;" />

    <PyParameter name="&#x22;asset_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;run_id&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;error_message&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;timestamp&#x22;" type="&#x22;Optional[datetime]&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
