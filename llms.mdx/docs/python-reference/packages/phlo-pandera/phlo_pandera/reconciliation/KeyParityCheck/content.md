# KeyParityCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/KeyParityCheck)



Check that source and target tables have matching keys.

This check compares distinct keys between source and target tables to catch
missing or extra rows even when row counts match. Useful for detecting
data alignment issues in joins and aggregations.

Attributes [#attributes]

<PyAttribute name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified source table name.
</PyAttribute>

<PyAttribute name="&#x22;key_columns&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Primary key or composite key columns used for alignment.
</PyAttribute>

<PyAttribute name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;">
  Column used for partition filtering.
</PyAttribute>

<PyAttribute name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;">
  Allowed fraction of missing keys (0.0 = exact match).
</PyAttribute>

<PyAttribute name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional WHERE clause to filter source data.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Get the check name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, df, context) -> QualityCheckResult&#x22;">
  Execute key parity check.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute key parity check.

        Args:
            df: Target DataFrame with key data.
            context: Runtime context with resources and partition info.

        Returns:
            QualityCheckResult with key comparison results.

        """
        missing_columns = [column for column in self.key_columns if column not in df.columns]
        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="key_parity_check",
                metric_value=None,
                failure_message=f"Missing key columns in target data: {missing_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_source_query(partition_key)
        source_rows = self._get_source_rows(context, source_query)

        if source_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="key_parity_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source keys from {self.source_table}",
            )

        source_keys = {tuple(row) for row in source_rows}
        target_keys = {
            tuple(row)
            for row in df[self.key_columns].drop_duplicates().itertuples(index=False, name=None)
        }

        missing_in_target = source_keys - target_keys
        missing_in_source = target_keys - source_keys

        total_keys = len(source_keys.union(target_keys))
        mismatch_count = len(missing_in_target) + len(missing_in_source)
        mismatch_pct = mismatch_count / total_keys if total_keys else 0.0

        passed = mismatch_pct <= self.tolerance

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Key parity check failed: {len(missing_in_target)} missing in target, "
                f"{len(missing_in_source)} missing in source "
                f"(mismatch: {mismatch_pct:.2%}, tolerance: {self.tolerance:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="key_parity_check",
            metric_value={
                "missing_in_target": len(missing_in_target),
                "missing_in_source": len(missing_in_source),
                "total_keys": total_keys,
                "mismatch_pct": float(mismatch_pct),
            },
            metadata={
                "source_table": self.source_table,
                "key_columns": self.key_columns,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "query": source_query,
                "sample_missing_in_target": [str(key) for key in list(missing_in_target)[:10]],
                "sample_missing_in_source": [str(key) for key in list(missing_in_source)[:10]],
            },
            failure_message=failure_msg,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
      Target DataFrame with key data.
    </PyParameter>

    <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext | None&#x22;" value="undefined">
      Runtime context with resources and partition info.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_pandera.checks.QualityCheckResult&#x22;">
    QualityCheckResult with key comparison results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_source_query&#x22;" type="&#x22;(self, partition_key) -> str&#x22;">
  Build SQL query to fetch distinct source keys.

  <PySourceCode>
    ```python
    def _build_source_query(self, partition_key: str | None) -> str:
        """Build SQL query to fetch distinct source keys.

        Args:
            partition_key: Optional partition key for filtering.

        Returns:
            SQL query string for fetching distinct keys.

        """
        select_cols = ", ".join(self.key_columns)
        query = f"SELECT DISTINCT {select_cols} FROM {self.source_table}"

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
    SQL query string for fetching distinct keys.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_source_rows&#x22;" type="&#x22;(self, context, query) -> list[tuple] | None&#x22;">
  Execute query to fetch source keys.

  <PySourceCode>
    ```python
    def _get_source_rows(self, context: RuntimeContext | None, query: str) -> list[tuple] | None:
        """Execute query to fetch source keys.

        Args:
            context: Runtime context with Trino resource.
            query: SQL query to execute.

        Returns:
            List of key tuples, or None if query failed.

        """
        try:
            if context is None:
                return None
            trino = _get_context_resource(context, "trino")
            if trino is not None:
                result = trino.execute_query(query)
                if result is not None:
                    return [tuple(row) for row in result]
        except Exception as exc:
            if context and context.logger:
                context.logger.warning("source_keys_query_failed", query=query, error=str(exc))
            return None
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

  <PyFunctionReturn type="&#x22;list[tuple] | None&#x22;">
    List of key tuples, or None if query failed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_table, key_columns, partition_column='_phlo_partition_date', tolerance=0.0, where_clause=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;key_columns&#x22;" type="&#x22;list[str]&#x22;" value="null" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;" />

    <PyParameter name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
