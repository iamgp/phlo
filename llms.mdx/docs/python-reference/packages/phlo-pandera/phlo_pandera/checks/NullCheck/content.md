# NullCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/NullCheck)



Check that specified columns have no null values.

This check validates that one or more columns contain no null (NaN/None)
values, or that the percentage of null values does not exceed a configurable
threshold.

Attributes [#attributes]

<PyAttribute name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="null">
  List of column names that must not contain nulls.
</PyAttribute>

<PyAttribute name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Maximum fraction of nulls allowed (0.0 = no nulls allowed,
  0.05 = up to 5% nulls allowed). Defaults to 0.0.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute null check on DataFrame.

  Iterates through all specified columns, checking for null values and
  calculating null percentages. Returns detailed metadata about null
  counts per column and sample rows containing nulls.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute null check on DataFrame.

        Iterates through all specified columns, checking for null values and
        calculating null percentages. Returns detailed metadata about null
        counts per column and sample rows containing nulls.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether all columns pass the null
            check within the specified threshold.

        """
        null_counts = {}
        null_percentages = {}
        failures = []
        sample_rows: list[dict[str, Any]] = []

        for column in self.columns:
            if column not in df.columns:
                failures.append(f"Column '{column}' not found in DataFrame")
                continue

            null_count = df[column].isna().sum()
            null_pct = null_count / len(df) if len(df) > 0 else 0.0

            null_counts[column] = int(null_count)
            null_percentages[column] = float(null_pct)

            if null_pct > self.allow_threshold:
                failures.append(
                    f"Column '{column}' has {null_pct:.2%} nulls "
                    f"(threshold: {self.allow_threshold:.2%})"
                )

                if not sample_rows:
                    existing_columns = [c for c in self.columns if c in df.columns]
                    if existing_columns:
                        sample_rows = extract_sample_rows(df, df[column].isna(), existing_columns)

        passed = len(failures) == 0

        return QualityCheckResult(
            passed=passed,
            metric_name="null_check",
            metric_value=null_counts,
            metadata={
                "null_counts": null_counts,
                "null_percentages": null_percentages,
                "threshold": self.allow_threshold,
                "columns_checked": self.columns,
                "sample_rows": sample_rows,
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
    QualityCheckResult indicating whether all columns pass the null
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
