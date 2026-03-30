# UniqueCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/UniqueCheck)



Check that specified columns have unique values (no duplicates).

This check validates that the combination of values across one or more
columns is unique across all rows. It supports threshold parameters that
allow a configurable percentage of duplicate rows.

Attributes [#attributes]

<PyAttribute name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="null">
  List of column names that must have unique combinations.
</PyAttribute>

<PyAttribute name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Maximum fraction of duplicates allowed (0.0 = exact
  uniqueness required, 0.05 = 5% duplicates allowed). Defaults to 0.0.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute uniqueness check on DataFrame.

  Uses pandas `duplicated()` method to identify duplicate rows based
  on the specified column combination. Calculates duplicate percentage
  and provides sample duplicate rows for debugging.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute uniqueness check on DataFrame.

        Uses pandas ``duplicated()`` method to identify duplicate rows based
        on the specified column combination. Calculates duplicate percentage
        and provides sample duplicate rows for debugging.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the columns have unique
            values within the specified threshold.

        """
        missing_columns = [col for col in self.columns if col not in df.columns]

        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="unique_check",
                metric_value=None,
                failure_message=f"Columns not found: {', '.join(missing_columns)}",
            )

        # Check for duplicates
        duplicates = df.duplicated(subset=self.columns, keep=False)
        duplicate_count = duplicates.sum()
        duplicate_pct = duplicate_count / len(df) if len(df) > 0 else 0.0

        passed = duplicate_pct <= self.allow_threshold

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Found {duplicate_count} duplicate rows ({duplicate_pct:.2%}) "
                f"in columns {self.columns} (threshold: {self.allow_threshold:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="unique_check",
            metric_value={"duplicate_count": int(duplicate_count)},
            metadata={
                "duplicate_count": int(duplicate_count),
                "duplicate_percentage": float(duplicate_pct),
                "threshold": self.allow_threshold,
                "columns_checked": self.columns,
                "total_rows": len(df),
                "sample_rows": [
                    {"row_index": idx if isinstance(idx, int) else str(idx), **row.to_dict()}
                    for idx, row in df.loc[duplicates, self.columns].head(20).iterrows()
                ],
            },
            failure_message=failure_msg,
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
    QualityCheckResult indicating whether the columns have unique
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, columns, allow_threshold=0.0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="null" />

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
