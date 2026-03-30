# RangeCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/RangeCheck)



Check that numeric column values are within specified range.

This check validates that all values in a numeric column fall within
an inclusive range defined by minimum and maximum values. It supports
optional thresholds that allow a percentage of out-of-range values.

Attributes [#attributes]

<PyAttribute name="&#x22;column&#x22;" type="&#x22;str&#x22;" value="null">
  Column name to validate.
</PyAttribute>

<PyAttribute name="&#x22;min_value&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;">
  Minimum allowed value (inclusive). None disables lower bound.
</PyAttribute>

<PyAttribute name="&#x22;max_value&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;">
  Maximum allowed value (inclusive). None disables upper bound.
</PyAttribute>

<PyAttribute name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Maximum fraction of out-of-range values allowed
  (0.0 = no violations allowed, 0.01 = 1% allowed). Defaults to 0.0.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute range check on DataFrame.

  Validates that values in the specified column fall within the defined
  range. Calculates actual min/max values and counts violations.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute range check on DataFrame.

        Validates that values in the specified column fall within the defined
        range. Calculates actual min/max values and counts violations.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the column values are within
            range, with detailed statistics about violations.

        """
        if self.column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="range_check",
                metric_value=None,
                failure_message=f"Column '{self.column}' not found in DataFrame",
            )

        column_data = df[self.column].dropna()

        if len(column_data) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="range_check",
                metric_value={"min": None, "max": None, "out_of_range": 0},
                metadata={"note": "No non-null values to check"},
            )

        # Check range violations
        violations = pd.Series([False] * len(column_data), index=column_data.index)

        if self.min_value is not None:
            violations |= column_data < self.min_value

        if self.max_value is not None:
            violations |= column_data > self.max_value

        violation_count = violations.sum()
        violation_pct = violation_count / len(column_data)

        passed = violation_pct <= self.allow_threshold

        actual_min = float(column_data.min())
        actual_max = float(column_data.max())

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Column '{self.column}' has {violation_pct:.2%} out-of-range values "
                f"(threshold: {self.allow_threshold:.2%}). "
                f"Expected range: [{self.min_value}, {self.max_value}], "
                f"Actual range: [{actual_min}, {actual_max}]"
            )

        sample_rows = (
            extract_sample_rows(df, violations, [self.column]) if violation_count > 0 else []
        )

        return QualityCheckResult(
            passed=passed,
            metric_name="range_check",
            metric_value={
                "min": actual_min,
                "max": actual_max,
                "out_of_range": int(violation_count),
            },
            metadata={
                "expected_min": self.min_value,
                "expected_max": self.max_value,
                "actual_min": actual_min,
                "actual_max": actual_max,
                "violation_count": int(violation_count),
                "violation_percentage": float(violation_pct),
                "out_of_range": int(violation_count),
                "threshold": self.allow_threshold,
                "sample_rows": sample_rows,
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
    QualityCheckResult indicating whether the column values are within
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, column, min_value=None, max_value=None, allow_threshold=0.0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;min_value&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;max_value&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
