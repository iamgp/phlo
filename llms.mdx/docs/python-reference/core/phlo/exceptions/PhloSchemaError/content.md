# PhloSchemaError (/docs/python-reference/core/phlo/exceptions/PhloSchemaError)



Raised when schema configuration is invalid.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, suggestions=None)&#x22;">
  Initialize a schema error.

  <PySourceCode>
    ```python
    def __init__(self, message: str, suggestions: list[str] | None = None):
        """Initialize a schema error.

        Args:
            message: Description of the schema issue.
            suggestions: Optional remediation suggestions.
        """
        super().__init__(
            message=message,
            code=PhloErrorCode.SCHEMA_MISMATCH,
            suggestions=suggestions,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Description of the schema issue.
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional remediation suggestions.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
