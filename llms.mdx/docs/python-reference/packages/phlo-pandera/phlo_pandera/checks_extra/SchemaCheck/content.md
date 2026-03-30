# SchemaCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/SchemaCheck)



Check that DataFrame matches a Pandera schema.

This check validates that a DataFrame conforms to a Pandera DataFrameModel
schema, including type validation, constraint checking (min, max, regex, etc.),
and nullability verification. It uses lazy validation to collect all errors
rather than failing on the first issue.

Attributes [#attributes]

<PyAttribute name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="null">
  Pandera DataFrameModel class to validate against (not an instance).
</PyAttribute>

<PyAttribute name="&#x22;lazy&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
  Whether to use lazy validation to collect all errors. Default True.
  When True, all schema violations are collected and reported.
  When False, validation stops at the first error.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute schema check on DataFrame.

  Validates the DataFrame against the configured Pandera schema using
  lazy validation to collect all validation errors. Groups failures by
  column and check type for detailed reporting.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute schema check on DataFrame.

        Validates the DataFrame against the configured Pandera schema using
        lazy validation to collect all validation errors. Groups failures by
        column and check type for detailed reporting.

        Args:
            df: DataFrame to validate against the schema.
            context: Runtime context for logging and resources.

        Returns:
            QualityCheckResult indicating schema validity with detailed failure
            information when validation fails.

        Raises:
            Exception: Catches and logs unexpected errors, returning a failed result.

        """
        try:
            # Validate with Pandera
            self.schema.validate(df, lazy=self.lazy)

            return QualityCheckResult(
                passed=True,
                metric_name="schema_check",
                metric_value={"schema_valid": True},
                metadata={
                    "schema_name": getattr(self.schema, "__name__", str(type(self.schema))),
                    "rows_validated": len(df),
                    "columns_validated": len(df.columns),
                },
            )

        except pa_errors.SchemaErrors as err:
            failure_cases = err.failure_cases

            failures_by_column = failure_cases.groupby("column").size().to_dict()
            failures_by_check = failure_cases.groupby("check").size().to_dict()

            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={
                    "schema_name": getattr(self.schema, "__name__", str(type(self.schema))),
                    "rows_evaluated": len(df),
                    "failed_checks": len(failure_cases),
                    "failures_by_column": failures_by_column,
                    "failures_by_check": failures_by_check,
                    "sample_failures": failure_cases.head(10).to_dict(orient="records"),
                },
                failure_message=f"Schema validation failed with {len(failure_cases)} errors",
            )

        except Exception as exc:
            logger.exception(
                "schema_check_execution_failed",
                schema_name=getattr(self.schema, "__name__", type(self.schema).__name__),
                row_count=len(df),
                column_count=len(df.columns),
            )
            return QualityCheckResult(
                passed=False,
                metric_name="schema_check",
                metric_value={"schema_valid": False},
                metadata={"error": str(exc)},
                failure_message=f"Unexpected error during schema validation: {exc}",
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      DataFrame to validate against the schema.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context for logging and resources.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult indicating schema validity with detailed failure
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, schema, lazy=True) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;lazy&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
