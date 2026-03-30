# PhloIngestionError (/docs/python-reference/core/phlo/exceptions/PhloIngestionError)



Raised when data ingestion fails.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, suggestions=None, cause=None)&#x22;">
  Initialize an ingestion error.

  <PySourceCode>
    ```python
    def __init__(
        self,
        message: str,
        suggestions: list[str] | None = None,
        cause: Exception | None = None,
    ):
        """Initialize an ingestion error.

        Args:
            message: Description of the ingestion failure.
            suggestions: Optional remediation suggestions.
            cause: Optional underlying exception.
        """
        super().__init__(
            message=message,
            code=PhloErrorCode.INGESTION_FAILED,
            suggestions=suggestions,
            cause=cause,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Description of the ingestion failure.
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional remediation suggestions.
    </PyParameter>

    <PyParameter name="&#x22;cause&#x22;" type="&#x22;Exception | None&#x22;" value="&#x22;None&#x22;">
      Optional underlying exception.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
