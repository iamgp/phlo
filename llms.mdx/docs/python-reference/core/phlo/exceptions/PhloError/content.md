# PhloError (/docs/python-reference/core/phlo/exceptions/PhloError)



Base exception for Phlo framework errors.

All Phlo exceptions include:

* Error code for searchability
* Contextual error message
* Suggested actions to resolve
* Link to documentation

Example:
raise PhloError(
message="unique\_key 'observation\_id' not found in schema",
code=PhloErrorCode.SCHEMA\_MISMATCH,
suggestions=\[
"Check that unique\_key matches a field in validation\_schema",
"Available fields: id, city, temperature, timestamp",
]
)

Attributes [#attributes]

<PyAttribute name="&#x22;code&#x22;" type="null" value="&#x22;code&#x22;" />

<PyAttribute name="&#x22;suggestions&#x22;" type="null" value="&#x22;suggestions or []&#x22;" />

<PyAttribute name="&#x22;cause&#x22;" type="null" value="&#x22;cause&#x22;" />

<PyAttribute name="&#x22;doc_url&#x22;" type="null" value="&#x22;f'https://docs.phlo.dev/errors/{code.value}'&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, code, suggestions=None, cause=None)&#x22;">
  Initialize PhloError.

  <PySourceCode>
    ```python
    def __init__(
        self,
        message: str,
        code: PhloErrorCode,
        suggestions: list[str] | None = None,
        cause: Exception | None = None,
    ):
        """
        Initialize PhloError.

        Args:
            message: Clear description of what went wrong
            code: Error code from PhloErrorCode enum
            suggestions: List of suggested actions to resolve the error
            cause: Original exception that caused this error (if wrapping)
        """
        self.code = code
        self.suggestions = suggestions or []
        self.cause = cause
        self.doc_url = f"https://docs.phlo.dev/errors/{code.value}"

        # Build formatted error message
        full_message = self._format_message(message)

        super().__init__(full_message)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Clear description of what went wrong
    </PyParameter>

    <PyParameter name="&#x22;code&#x22;" type="&#x22;PhloErrorCode&#x22;" value="undefined">
      Error code from PhloErrorCode enum
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      List of suggested actions to resolve the error
    </PyParameter>

    <PyParameter name="&#x22;cause&#x22;" type="&#x22;Exception | None&#x22;" value="&#x22;None&#x22;">
      Original exception that caused this error (if wrapping)
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_format_message&#x22;" type="&#x22;(self, message) -> str&#x22;">
  Format error message with code, suggestions, and documentation link.

  <PySourceCode>
    ```python
    def _format_message(self, message: str) -> str:
        """Format error message with code, suggestions, and documentation link."""

        lines = [
            f"{self.__class__.__name__} ({self.code.value}): {message}",
        ]

        if self.suggestions:
            lines.append("")
            lines.append("Suggested actions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        if self.cause:
            lines.append("")
            lines.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")

        lines.append("")
        lines.append(f"Documentation: {self.doc_url}")

        return "\n".join(lines)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>
