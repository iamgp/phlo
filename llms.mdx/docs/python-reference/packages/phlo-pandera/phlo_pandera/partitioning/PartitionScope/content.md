# PartitionScope (/docs/python-reference/packages/phlo-pandera/phlo_pandera/partitioning/PartitionScope)



Partition filter scope for SQL quality checks.

Defines how a quality check query should be scoped to specific data partitions.
The scope can target an explicit partition key, a rolling time window, or
the full table.

Attributes [#attributes]

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null">
  Explicit partition key to target, typically in YYYY-MM-DD
  format. When provided, the check is scoped to this specific partition.
</PyAttribute>

<PyAttribute name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="null">
  Column name used for partition filtering in WHERE clauses.
  Default is "\_phlo\_partition\_date".
</PyAttribute>

<PyAttribute name="&#x22;rolling_window_days&#x22;" type="&#x22;int | None&#x22;" value="null">
  Optional rolling lookback window in days. When set
  and partition\_key is None, filters to the last N days of data.
</PyAttribute>

<PyAttribute name="&#x22;full_table&#x22;" type="&#x22;bool&#x22;" value="null">
  If True, skip all partition filtering and scan the full table.
  Useful for historical analysis or small dimension tables.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, partition_key, partition_column, rolling_window_days, full_table) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="null" />

    <PyParameter name="&#x22;partition_column&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;rolling_window_days&#x22;" type="&#x22;int | None&#x22;" value="null" />

    <PyParameter name="&#x22;full_table&#x22;" type="&#x22;bool&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
