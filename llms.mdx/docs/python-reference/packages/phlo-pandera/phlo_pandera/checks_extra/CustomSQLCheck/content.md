# CustomSQLCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/CustomSQLCheck)



Execute arbitrary SQL to validate data.

This check enables complex validation logic by executing custom SQL queries
against the data using DuckDB. The SQL should return a single boolean column
where True indicates a valid row and False indicates a violation.

This is useful for cross-column validations, business rule checks, or any
validation that cannot be expressed with the standard check types.

Attributes [#attributes]

<PyAttribute name="&#x22;name_&#x22;" type="&#x22;str&#x22;" value="null">
  Name of this check for identification in results.
</PyAttribute>

<PyAttribute name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="null">
  SQL query that returns a boolean column. True = valid, False = violation.
  The DataFrame is registered as a table named "data".
</PyAttribute>

<PyAttribute name="&#x22;expected&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
  Expected boolean result for valid rows. Default True.
</PyAttribute>

<PyAttribute name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Maximum fraction of failures allowed (0.0 = no failures
  allowed, 0.05 = 5% allowed). Default 0.0.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute custom SQL check on DataFrame.

  Registers the DataFrame as a DuckDB table named "data" and executes the
  provided SQL query. Counts rows where the result doesn't match the expected
  value and determines pass/fail based on the threshold.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute custom SQL check on DataFrame.

        Registers the DataFrame as a DuckDB table named "data" and executes the
        provided SQL query. Counts rows where the result doesn't match the expected
        value and determines pass/fail based on the threshold.

        Args:
            df: DataFrame to validate. Registered as "data" table in DuckDB.
            context: Runtime context for logging.

        Returns:
            QualityCheckResult with failure counts and statistics.

        Raises:
            ImportError: If DuckDB is not available.
            Exception: Catches SQL execution errors and returns failed result.

        """
        try:
            # Execute SQL in pandas context
            # This requires DuckDB or similar for SQL execution
            import duckdb

            # Register DataFrame as a view
            conn = duckdb.connect(":memory:")
            conn.register("data", df)

            # Execute the check query
            result = conn.execute(self.sql).fetchall()

            if not result:
                return QualityCheckResult(
                    passed=True,
                    metric_name=self.name_,
                    metric_value={"rows_checked": 0},
                    metadata={"note": "No data returned from check query"},
                )

            # Count failures (where result is False or not expected value)
            failures = sum(1 for (row_result,) in result if row_result != self.expected)
            failure_pct = failures / len(result) if result else 0.0

            passed = failure_pct <= self.allow_threshold

            failure_msg = None
            if not passed:
                failure_msg = (
                    f"Custom SQL check failed: {failure_pct:.2%} of rows failed validation "
                    f"(threshold: {self.allow_threshold:.2%})"
                )

            return QualityCheckResult(
                passed=passed,
                metric_name=self.name_,
                metric_value={"failures": failures, "total": len(result)},
                metadata={
                    "failure_count": failures,
                    "total_rows": len(result),
                    "failure_percentage": float(failure_pct),
                    "threshold": self.allow_threshold,
                },
                failure_message=failure_msg,
            )

        except ImportError:
            logger.warning(
                "custom_sql_check_duckdb_missing",
                check_name=self.name_,
            )
            return QualityCheckResult(
                passed=False,
                metric_name=self.name_,
                metric_value=None,
                failure_message="DuckDB not available for custom SQL check",
            )
        except Exception as exc:
            logger.exception(
                "custom_sql_check_execution_failed",
                check_name=self.name_,
                expected=self.expected,
                sql_length=len(self.sql),
            )
            return QualityCheckResult(
                passed=False,
                metric_name=self.name_,
                metric_value=None,
                metadata={"error": str(exc)},
                failure_message=f"Custom SQL check failed: {exc}",
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame to validate. Registered as "data" table in DuckDB.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context for logging.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult with failure counts and statistics.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name_, sql, expected=True, allow_threshold=0.0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name_&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;expected&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />

    <PyParameter name="&#x22;allow_threshold&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
