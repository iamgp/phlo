# MultiAggregateConsistencyCheck (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/MultiAggregateConsistencyCheck)



Check that multiple aggregates match source data.

This check compares multiple aggregates in a single query to reduce
repeated scans of the source table. More efficient than running multiple
AggregateConsistencyCheck instances separately.

Attributes [#attributes]

<PyAttribute name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null">
  Fully qualified source table name.
</PyAttribute>

<PyAttribute name="&#x22;aggregates&#x22;" type="&#x22;list[AggregateSpec]&#x22;" value="null">
  List of AggregateSpec defining aggregates to compare.
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
  Execute multi-aggregate consistency check.

  <PySourceCode>
    ```python
    def execute(self, df: pd.DataFrame, context: RuntimeContext | None) -> QualityCheckResult:
        """Execute multi-aggregate consistency check.

        Args:
            df: Target DataFrame with aggregated data.
            context: Runtime context with resources and partition info.

        Returns:
            QualityCheckResult with comparison results.

        """
        if not self.aggregates:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message="No aggregates provided for comparison",
            )

        aggregate_names = [agg.name for agg in self.aggregates]
        if len(set(aggregate_names)) != len(aggregate_names):
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message="Aggregate names must be unique",
            )

        missing_target_columns = [
            agg.target_column for agg in self.aggregates if agg.target_column not in df.columns
        ]
        if missing_target_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Missing target columns: {missing_target_columns}",
            )

        missing_group_columns = [column for column in self.group_by if column not in df.columns]
        if missing_group_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Missing group_by columns: {missing_group_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_source_query(partition_key)
        source_values = self._get_source_aggregates(context, source_query)

        if source_values is None:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source aggregates from {self.source_table}",
            )

        mismatches: list[dict[str, Any]] = []

        if self.group_by:
            target_keys = {
                tuple(row)
                for row in df[self.group_by].drop_duplicates().itertuples(index=False, name=None)
            }
            source_keys = set(source_values.keys())

            missing_in_target = source_keys - target_keys
            missing_in_source = target_keys - source_keys

            for key in missing_in_source:
                for aggregate in self.aggregates:
                    mismatches.append(
                        {
                            "group_key": str(key),
                            "aggregate": aggregate.name,
                            "reason": "missing_in_source",
                        }
                    )

            for key in missing_in_target:
                for aggregate in self.aggregates:
                    mismatches.append(
                        {
                            "group_key": str(key),
                            "aggregate": aggregate.name,
                            "reason": "missing_in_target",
                        }
                    )

            for _, row in df.iterrows():
                group_key = tuple(row[col] for col in self.group_by)
                if group_key not in source_values:
                    continue
                source_row = source_values[group_key]
                for aggregate in self.aggregates:
                    target_value = row[aggregate.target_column]
                    source_value = source_row.get(aggregate.name)
                    if not self._values_match(target_value, source_value):
                        mismatches.append(
                            {
                                "group_key": str(group_key),
                                "aggregate": aggregate.name,
                                "target": target_value,
                                "source": source_value,
                            }
                        )
        else:
            target_totals = {agg.name: df[agg.target_column].sum() for agg in self.aggregates}
            source_total = source_values.get(()) if source_values else None
            for aggregate in self.aggregates:
                target_value = target_totals.get(aggregate.name)
                source_value = source_total.get(aggregate.name) if source_total else None
                if not self._values_match(target_value, source_value):
                    mismatches.append(
                        {
                            "aggregate": aggregate.name,
                            "target": target_value,
                            "source": source_value,
                        }
                    )

        passed = len(mismatches) == 0
        total_checks = max(len(self.aggregates), 1)
        if self.group_by:
            total_checks = max(len(source_values), len(df)) * len(self.aggregates)

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Multi-aggregate consistency check failed: {len(mismatches)} mismatches "
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
            metric_name="multi_aggregate_consistency_check",
            metric_value={"mismatches": len(mismatches), "total_checked": total_checks},
            metadata={
                "source_table": self.source_table,
                "aggregates": [aggregate.__dict__ for aggregate in self.aggregates],
                "group_by": self.group_by,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "query": source_query,
                "sample_mismatches": mismatches[:10],
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
    QualityCheckResult with comparison results.
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
        aggregate_exprs = ", ".join(
            f"{aggregate.expression} as {aggregate.name}" for aggregate in self.aggregates
        )
        query = f"SELECT {select_cols}, {aggregate_exprs} FROM {self.source_table}"

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

<PyFunction name="&#x22;_get_source_aggregates&#x22;" type="&#x22;(self, context, query) -> dict[tuple, dict[str, Any]] | None&#x22;">
  Execute query to get source aggregate values.

  <PySourceCode>
    ```python
    def _get_source_aggregates(
        self, context: RuntimeContext | None, query: str
    ) -> dict[tuple, dict[str, Any]] | None:
        """Execute query to get source aggregate values.

        Args:
            context: Runtime context with Trino resource.
            query: SQL query to execute.

        Returns:
            Dictionary mapping group keys to aggregate dicts, or None if query failed.

        """
        try:
            if context is None:
                return None
            trino = _get_context_resource(context, "trino")
            if trino is not None:
                result = trino.execute_query(query)
                if result:
                    values: dict[tuple, dict[str, Any]] = {}
                    for row in result:
                        if self.group_by:
                            key = tuple(row[: len(self.group_by)])
                            agg_values = {
                                aggregate.name: row[len(self.group_by) + idx]
                                for idx, aggregate in enumerate(self.aggregates)
                            }
                        else:
                            key = ()
                            agg_values = {
                                aggregate.name: row[idx]
                                for idx, aggregate in enumerate(self.aggregates)
                            }
                        values[key] = agg_values
                    return values

            return None
        except Exception as exc:
            if context and context.logger:
                context.logger.warning(
                    "source_aggregate_query_failed",
                    query=query,
                    error=str(exc),
                )
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

  <PyFunctionReturn type="&#x22;dict[tuple, dict[str, Any]] | None&#x22;">
    Dictionary mapping group keys to aggregate dicts, or None if query failed.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source_table, aggregates, partition_column='_phlo_partition_date', group_by=list(), tolerance=0.0, absolute_tolerance=None, where_clause=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source_table&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;aggregates&#x22;" type="&#x22;list[AggregateSpec]&#x22;" value="null" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="&#x22;'_phlo_partition_date'&#x22;" />

    <PyParameter name="&#x22;group_by&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;tolerance&#x22;" type="&#x22;float&#x22;" value="&#x22;0.0&#x22;" />

    <PyParameter name="&#x22;absolute_tolerance&#x22;" type="&#x22;int | float | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;where_clause&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
