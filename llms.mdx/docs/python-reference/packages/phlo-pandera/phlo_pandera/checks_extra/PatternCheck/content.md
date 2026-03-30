# PatternCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/PatternCheck)



Check that string column values match a regex pattern.

This check validates that all non-null values in a string column match
a specified regular expression pattern. It's useful for format validation
such as email addresses, phone numbers, postal codes, IDs, etc.

Supports configurable thresholds to allow a percentage of non-matching
values, and case sensitivity can be controlled via a flag.

Attributes [#attributes]

<PyAttribute name="&#x22;column&#x22;" type="&#x22;str&#x22;" value="null">
  Column name to validate.
</PyAttribute>

<PyAttribute name="&#x22;pattern&#x22;" type="&#x22;str&#x22;" value="null">
  Regular expression pattern that values must match.
</PyAttribute>

<PyAttribute name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Maximum fraction of non-matching values allowed
  (0.0 = all values must match, 0.05 = 5% can fail). Default 0.0.
</PyAttribute>

<PyAttribute name="&#x22;case_sensitive&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
  Whether pattern matching is case sensitive. Default True.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute pattern check on DataFrame.

  Compiles the regex pattern (with optional case insensitivity) and matches
  it against all non-null string values in the specified column. Calculates
  match statistics and provides sample non-matching values for debugging.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute pattern check on DataFrame.

        Compiles the regex pattern (with optional case insensitivity) and matches
        it against all non-null string values in the specified column. Calculates
        match statistics and provides sample non-matching values for debugging.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context for logging.

        Returns:
            QualityCheckResult indicating whether the pattern matches the
            configured percentage of values.

        """
        if self.column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="pattern_check",
                metric_value=None,
                failure_message=f"Column '{self.column}' not found in DataFrame",
            )

        column_data = df[self.column].dropna().astype(str)

        if len(column_data) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="pattern_check",
                metric_value={"matches": 0, "non_matches": 0},
                metadata={"note": "No non-null values to check"},
            )

        import re

        flags = 0 if self.case_sensitive else re.IGNORECASE
        pattern_compiled = re.compile(self.pattern, flags)

        matches = column_data.str.match(pattern_compiled, na=False)
        non_match_count = (~matches).sum()
        non_match_pct = non_match_count / len(column_data)

        passed = non_match_pct <= self.allow_threshold

        failure_msg = None
        if not passed:
            sample_non_matches = column_data[~matches].head(5).tolist()
            failure_msg = (
                f"Column '{self.column}' has {non_match_pct:.2%} values not matching pattern "
                f"(threshold: {self.allow_threshold:.2%}). "
                f"Sample non-matches: {sample_non_matches}"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="pattern_check",
            metric_value={
                "matches": int(matches.sum()),
                "non_matches": int(non_match_count),
            },
            metadata={
                "pattern": self.pattern,
                "case_sensitive": self.case_sensitive,
                "match_count": int(matches.sum()),
                "non_match_count": int(non_match_count),
                "non_match_percentage": float(non_match_pct),
                "threshold": self.allow_threshold,
                "total_rows": len(column_data),
                "sample_rows": [
                    {"row_index": idx if isinstance(idx, int) else str(idx), self.column: value}
                    for idx, value in column_data[~matches].head(20).items()
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
      Runtime context for logging.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult indicating whether the pattern matches the
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, column, pattern, allow_threshold=0.0, case_sensitive=True) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;pattern&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;case_sensitive&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
