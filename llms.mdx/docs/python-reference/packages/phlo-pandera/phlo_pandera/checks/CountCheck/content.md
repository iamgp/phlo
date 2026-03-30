# CountCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/CountCheck)



Check that row count meets expectations.

This check validates that the number of rows in a dataset falls within
expected bounds. It's useful for detecting empty datasets, unexpected
data volumes, or significant data loss.

Attributes [#attributes]

<PyAttribute name="&#x22;min_rows&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  Minimum expected row count. None disables minimum check.
</PyAttribute>

<PyAttribute name="&#x22;max_rows&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  Maximum expected row count. None disables maximum check.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute count check on DataFrame.

  Counts total rows in the DataFrame and validates against configured
  minimum and maximum bounds.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute count check on DataFrame.

        Counts total rows in the DataFrame and validates against configured
        minimum and maximum bounds.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the row count is within
            the specified bounds.

        """
        row_count = len(df)

        failures = []

        if self.min_rows is not None and row_count < self.min_rows:
            failures.append(f"Row count {row_count} is below minimum {self.min_rows}")

        if self.max_rows is not None and row_count > self.max_rows:
            failures.append(f"Row count {row_count} is above maximum {self.max_rows}")

        passed = len(failures) == 0

        return QualityCheckResult(
            passed=passed,
            metric_name="count_check",
            metric_value={"row_count": row_count},
            metadata={
                "row_count": row_count,
                "min_rows": self.min_rows,
                "max_rows": self.max_rows,
            },
            failure_message="; ".join(failures) if failures else None,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame containing the data to validate.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context (unused but required by interface).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult indicating whether the row count is within
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, min_rows=None, max_rows=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;min_rows&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;max_rows&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
