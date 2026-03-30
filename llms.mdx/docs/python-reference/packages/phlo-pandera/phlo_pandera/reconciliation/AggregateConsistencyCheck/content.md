# AggregateConsistencyCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/AggregateConsistencyCheck)



Check that computed aggregates match source data.

This check verifies that aggregated values in a target table match the
expected computation from source data. Useful for validating sum, count,
average, and other aggregate transformations.

Attributes [#attributes]

<PyAttribute name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified source table name.
</PyAttribute>

<PyAttribute name="&#x22;aggregate_column&#x22;" type="&#x22;str&#x22;" value="null">
  Column in target table containing the aggregate value.
</PyAttribute>

<PyAttribute name="&#x22;source_expression&#x22;" type="&#x22;str&#x22;" value="null">
  SQL expression to compute from source
  (e.g., 'COUNT(\*)', 'SUM(amount)', 'AVG(price)').
</PyAttribute>

<PyAttribute name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;">
  Column used for partition filtering.
</PyAttribute>

<PyAttribute name="&#x22;group_by&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Columns to group by when comparing aggregates.
</PyAttribute>

<PyAttribute name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Allowed percentage difference (0.0 = exact match).
</PyAttribute>

<PyAttribute name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;">
  Allowed absolute difference in values.
</PyAttribute>

<PyAttribute name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional WHERE clause to filter source data.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute aggregate consistency check.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute aggregate consistency check.

        Args:
            df: Target DataFrame with aggregated data.
            context: Runtime context with resources and partition info.

        Returns:
            QualityCheckResult with mismatch details.

        """
        if self.aggregate_column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Column '{self.aggregate_column}' not found in target data",
            )

        # Get partition key from context if available
        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key

        # Build source query
        source_query = self._build_source_query(partition_key)

        # Get expected values from source
        source_values = self._get_source_aggregates(context, source_query)

        if source_values is None:
            return QualityCheckResult(
                passed=False,
                metric_name="aggregate_consistency_check",
                metric_value=None,
                metadata={
                    "source_table": self.source_table,
                    "query": source_query,
                },
                failure_message=f"Failed to query source aggregates from {self.source_table}",
            )

        # Compare target vs source
        mismatches = []
        total_checks = 0

        if self.group_by:
            # Group-level comparison
            for _, row in df.iterrows():
                group_key = tuple(row[col] for col in self.group_by if col in df.columns)
                target_value = row[self.aggregate_column]

                # Find matching source value
                source_value = source_values.get(group_key)
                if source_value is not None:
                    total_checks += 1
                    if not self._values_match(target_value, source_value):
                        mismatches.append(
                            {
                                "group_key": str(group_key),
                                "target": target_value,
                                "source": source_value,
                            }
                        )
        else:
            # Single value comparison (sum of all)
            target_total = df[self.aggregate_column].sum()
            source_total = sum(source_values.values()) if source_values else 0
            total_checks = 1

            if not self._values_match(target_total, source_total):
                mismatches.append(
                    {
                        "target_total": target_total,
                        "source_total": source_total,
                    }
                )

        passed = len(mismatches) == 0

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Aggregate consistency check failed: {len(mismatches)} mismatches "
                f"out of {total_checks} checked (tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="aggregate_consistency_check",
            metric_value={
                "mismatches": len(mismatches),
                "total_checked": total_checks,
            },
            metadata={
                "source_table": self.source_table,
                "aggregate_column": self.aggregate_column,
                "source_expression": self.source_expression,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "query": source_query,
                "sample_mismatches": mismatches[:10],  # Limit to 10 samples
            },
            failure_message=failure_msg,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Target DataFrame with aggregated data.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with resources and partition info.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult with mismatch details.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_values_match&#x22;" type="&#x22;(self, target, source) -> bool&#x22;">
  Check if target and source values match within tolerance.

  <PySourceCode>
    ```python
    def _values_match(self, target: Any, source: Any) -> bool:
        """Check if target and source values match within tolerance.

        Args:
            target: Target value to compare.
            source: Source value to compare.

        Returns:
            True if values match within tolerance, False otherwise.

        """
        try:
            target_val = float(target) if target is not None else 0.0
            source_val = float(source) if source is not None else 0.0

            if source_val == 0 and target_val == 0:
                return True
            if source_val == 0:
                if self.absolute_tolerance is not None:
                    return abs(target_val) <= self.absolute_tolerance
                return False

            diff_pct = abs(target_val - source_val) / abs(source_val)
            if diff_pct <= self.tolerance:
                return True
            if self.absolute_tolerance is not None:
                return abs(target_val - source_val) <= self.absolute_tolerance
            return False
        except (TypeError, ValueError):
            return target == source
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;target&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Target value to compare.
    </PyParameter>

    <PyParameter name="&#x22;source&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Source value to compare.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if values match within tolerance, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_source_query&#x22;" type="&#x22;(self, partition_key) -> str&#x22;">
  Build SQL query to compute source aggregates.

  <PySourceCode>
    ```python
    def _build_source_query(self, partition_key: str | None) -> str:
        """Build SQL query to compute source aggregates.

        Args:
            partition_key: Optional partition key for filtering.

        Returns:
            SQL query string for computing aggregates.

        """
        select_cols = ", ".join(self.group_by) if self.group_by else "1 as grp"
        query = (
            f"SELECT {select_cols}, {self.source_expression} as agg_value FROM {self.source_table}"
        )

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        if self.where_clause:
            conditions.append(f"({self.where_clause})")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if self.group_by:
            query += " GROUP BY " + ", ".join(self.group_by)

        return query
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional partition key for filtering.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    SQL query string for computing aggregates.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_source_aggregates&#x22;" type="&#x22;(self, context, query) -> dict[tuple, Any] | None&#x22;">
  Execute query to get source aggregate values.

  <PySourceCode>
    ```python
    def _get_source_aggregates(
        self, context: RuntimeContext | None, query: str
    ) -> dict[tuple, Any] | None:
        """Execute query to get source aggregate values.

        Args:
            context: Runtime context with Trino resource.
            query: SQL query to execute.

        Returns:
            Dictionary mapping group keys to aggregate values, or None if query failed.

        """
        try:
            if context is None:
                return None
            trino = _get_context_resource(context, "trino")
            if trino is not None:
                result = trino.execute_query(query)
                if result:
                    # Build dict of group_key -> aggregate_value
                    values = {}
                    for row in result:
                        if self.group_by:
                            key = tuple(row[:-1])  # All but last column
                            values[key] = row[-1]  # Last column is aggregate
                        else:
                            values[()] = row[-1]
                    return values

            # For testing without Trino, return None
            return None

        except Exception as e:
            if context and context.logger:
                context.logger.warning("source_aggregate_query_failed", query=query, error=str(e))
            return None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with Trino resource.
    </PyParameter>

    <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
      SQL query to execute.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict[tuple, Any] | None&#x22;">
    Dictionary mapping group keys to aggregate values, or None if query failed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_table, aggregate_column, source_expression, partition_column='_phlo_partition_date', group_by=list(), tolerance=0.0, absolute_tolerance=None, where_clause=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;aggregate_column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;source_expression&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;" />

    <PyParameter name="&#x22;group_by&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
