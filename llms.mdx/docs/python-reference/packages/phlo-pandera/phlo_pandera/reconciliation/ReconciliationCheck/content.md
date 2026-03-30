# ReconciliationCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/ReconciliationCheck)



Check row count parity between source and target tables.

This check compares row counts between two tables to ensure data is not
lost or duplicated during transformation. Supports configurable tolerance
for acceptable differences.

Attributes [#attributes]

<PyAttribute name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified source table name (e.g., 'silver.stg\_events').
</PyAttribute>

<PyAttribute name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;">
  Column used for partition filtering. Default is
  "\_phlo\_partition\_date".
</PyAttribute>

<PyAttribute name="&#x22;check_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'rowcount_parity'&#x22;">
  Type of reconciliation to perform:

  * "rowcount\_parity": Exact count match within tolerance
  * "rowcount\_gte": Target must have at least as many rows as source
</PyAttribute>

<PyAttribute name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Allowed percentage difference (0.0 = exact match,
  0.05 = 5% tolerance). Default 0.0.
</PyAttribute>

<PyAttribute name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;">
  Allowed absolute difference in row counts.
  None disables this check. Default None.
</PyAttribute>

<PyAttribute name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional WHERE clause to filter source data.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute reconciliation check comparing row counts.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute reconciliation check comparing row counts.

        Args:
            df: Target DataFrame with data to validate.
            context: Runtime context with resources and partition info.

        Returns:
            QualityCheckResult with comparison results.

        """
        target_count = len(df)

        # Get partition key from context if available
        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        # Build the source count query
        source_query = self._build_source_query(partition_key)

        # Try to get source count from Trino
        source_count = self._get_source_count(context, source_query)

        if source_count is None:
            return QualityCheckResult(
                passed=False,
                metric_name="reconciliation_check",
                metric_value={"target_count": target_count, "source_count": None},
                metadata={
                    "source_table": self.source_table,
                    "query": source_query,
                    "note": "Could not query source table",
                },
                failure_message=f"Failed to query source table {self.source_table}",
            )

        # Calculate difference
        if source_count == 0 and target_count == 0:
            diff_pct = 0.0
        elif source_count == 0:
            diff_pct = 1.0  # 100% difference if source is empty but target is not
        else:
            diff_pct = abs(target_count - source_count) / source_count
        diff_abs = abs(target_count - source_count)

        # Determine pass/fail based on check type
        if self.check_type == "rowcount_parity":
            passed = diff_pct <= self.tolerance or (
                self.absolute_tolerance is not None and diff_abs <= self.absolute_tolerance
            )
        elif self.check_type == "rowcount_gte":
            # Target should have at least as many rows as source
            passed = target_count >= source_count * (1 - self.tolerance) or (
                self.absolute_tolerance is not None
                and target_count >= source_count - self.absolute_tolerance
            )
        else:
            passed = diff_pct <= self.tolerance or (
                self.absolute_tolerance is not None and diff_abs <= self.absolute_tolerance
            )

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Row count reconciliation failed: target has {target_count} rows, "
                f"source has {source_count} rows (diff: {diff_pct:.2%}, "
                f"tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="reconciliation_check",
            metric_value={
                "target_count": target_count,
                "source_count": source_count,
                "difference_pct": float(diff_pct),
                "difference_abs": int(diff_abs),
            },
            metadata={
                "source_table": self.source_table,
                "check_type": self.check_type,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "query": source_query,
            },
            failure_message=failure_msg,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Target DataFrame with data to validate.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with resources and partition info.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult with comparison results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_source_query&#x22;" type="&#x22;(self, partition_key) -> str&#x22;">
  Build SQL query to count source rows.

  <PySourceCode>
    ```python
    def _build_source_query(self, partition_key: str | None) -> str:
        """Build SQL query to count source rows.

        Args:
            partition_key: Optional partition key for filtering.

        Returns:
            SQL query string for counting source rows.

        """
        query = f"SELECT COUNT(*) FROM {self.source_table}"

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        if self.where_clause:
            conditions.append(f"({self.where_clause})")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

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
    SQL query string for counting source rows.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_source_count&#x22;" type="&#x22;(self, context, query) -> int | None&#x22;">
  Execute query to get source row count.

  <PySourceCode>
    ```python
    def _get_source_count(self, context: RuntimeContext | None, query: str) -> int | None:
        """Execute query to get source row count.

        Args:
            context: Runtime context with Trino resource.
            query: SQL query to execute.

        Returns:
            Row count as int, or None if query failed.

        """
        try:
            if context is None:
                return None
            trino = _get_context_resource(context, "trino")
            if trino is not None:
                result = trino.execute_query(query)
                if result and len(result) > 0:
                    return int(result[0][0])

        except Exception as e:
            if context and context.logger:
                context.logger.warning("source_query_failed", query=query, error=str(e))
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

  <PyFunctionReturn type="&#x22;int | None&#x22;">
    Row count as int, or None if query failed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_table, partition_column='_phlo_partition_date', check_type='rowcount_parity', tolerance=0.0, absolute_tolerance=None, where_clause=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;" />

    <PyParameter name="&#x22;check_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'rowcount_parity'&#x22;" />

    <PyParameter name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
