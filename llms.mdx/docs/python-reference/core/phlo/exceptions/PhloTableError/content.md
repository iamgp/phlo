# PhloTableError (/docs/python-reference/core/phlo/exceptions/PhloTableError)



Raised when Iceberg table operations fail.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, suggestions=None)&#x22;">
  Initialize a table operation error.

  <PySourceCode>
    ```python
    def __init__(self, message: str, suggestions: list[str] | None = None):
        """Initialize a table operation error.

        Args:
            message: Description of the table operation issue.
            suggestions: Optional remediation suggestions.
        """
        super().__init__(
            message=message,
            code=PhloErrorCode.TABLE_NOT_FOUND,
            suggestions=suggestions,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Description of the table operation issue.
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional remediation suggestions.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
