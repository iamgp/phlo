# FreshnessCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/FreshnessCheck)



Check that data is fresh (not stale).

This check validates that the most recent timestamp in a specified column
is within a maximum age threshold. It's useful for detecting stale data
or pipeline delays.

Attributes [#attributes]

<PyAttribute name="&#x22;timestamp_column&#x22;" type="&#x22;str&#x22;" value="null">
  Column name containing timestamps to check.
</PyAttribute>

<PyAttribute name="&#x22;max_age_hours&#x22;" type="&#x22;float&#x22;" value="null">
  Maximum age in hours for data to be considered fresh.
</PyAttribute>

<PyAttribute name="&#x22;reference_time&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;">
  Reference time to compare against. Defaults to the
  current time (datetime.now()).
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute freshness check on DataFrame.

  Converts the timestamp column to datetime, finds the most recent value,
  and calculates its age relative to the reference time.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute freshness check on DataFrame.

        Converts the timestamp column to datetime, finds the most recent value,
        and calculates its age relative to the reference time.

        Args:
            df: DataFrame containing the data to validate.
            context: Runtime context (unused but required by interface).

        Returns:
            QualityCheckResult indicating whether the data is fresh within
            the specified maximum age.

        """
        if self.timestamp_column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="freshness_check",
                metric_value=None,
                failure_message=f"Column '{self.timestamp_column}' not found in DataFrame",
            )

        # Convert to datetime if needed
        timestamp_data = pd.Series(pd.to_datetime(df[self.timestamp_column], errors="coerce"))

        if len(timestamp_data.dropna()) == 0:
            return QualityCheckResult(
                passed=True,
                metric_name="freshness_check",
                metric_value={"max_age_hours": None},
                metadata={"note": "No non-null timestamps to check"},
            )

        # Get most recent timestamp
        max_timestamp = timestamp_data.max()

        # Calculate age
        reference = self.reference_time or datetime.now(tz=max_timestamp.tzinfo)
        age = reference - max_timestamp
        age_hours = age.total_seconds() / 3600

        passed = age_hours <= self.max_age_hours

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Data is stale. Most recent timestamp is {age_hours:.2f} hours old "
                f"(threshold: {self.max_age_hours:.2f} hours)"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="freshness_check",
            metric_value={"max_age_hours": float(age_hours)},
            metadata={
                "max_timestamp": str(max_timestamp),
                "reference_time": str(reference),
                "age_hours": float(age_hours),
                "threshold_hours": self.max_age_hours,
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
    QualityCheckResult indicating whether the data is fresh within
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, timestamp_column, max_age_hours, reference_time=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;timestamp_column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;max_age_hours&#x22;" type="&#x22;float&#x22;" value="null" />

    <PyParameter name="&#x22;reference_time&#x22;" type="&#x22;datetime | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
