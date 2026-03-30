# PhloDiscoveryError (/docs/python-reference/core/phlo/exceptions/PhloDiscoveryError)



Raised when assets cannot be discovered by Dagster.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, suggestions=None)&#x22;">
  Initialize a discovery error.

  <PySourceCode>
    ```python
    def __init__(self, message: str, suggestions: list[str] | None = None):
        """Initialize a discovery error.

        Args:
            message: Description of the discovery failure.
            suggestions: Optional remediation suggestions.
        """
        super().__init__(
            message=message,
            code=PhloErrorCode.ASSET_NOT_DISCOVERED,
            suggestions=suggestions,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Description of the discovery failure.
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional remediation suggestions.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
