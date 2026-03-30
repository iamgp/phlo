# PhloCronError (/docs/python-reference/core/phlo/exceptions/PhloCronError)



Raised when cron expression is invalid.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, message, suggestions=None)&#x22;">
  Initialize a cron expression error.

  <PySourceCode>
    ```python
    def __init__(self, message: str, suggestions: list[str] | None = None):
        """Initialize a cron expression error.

        Args:
            message: Description of the cron validation issue.
            suggestions: Optional remediation suggestions. Defaults are used when omitted.
        """
        super().__init__(
            message=message,
            code=PhloErrorCode.INVALID_CRON,
            suggestions=suggestions
            or [
                "Use standard cron format: [minute] [hour] [day_of_month] [month] [day_of_week]",
                'Examples: "0 */1 * * *" (hourly), "0 0 * * *" (daily)',
                "Test your cron at: https://crontab.guru",
            ],
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Description of the cron validation issue.
    </PyParameter>

    <PyParameter name="&#x22;suggestions&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
      Optional remediation suggestions. Defaults are used when omitted.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>
