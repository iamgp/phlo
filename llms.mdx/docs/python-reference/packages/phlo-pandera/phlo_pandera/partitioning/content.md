# partitioning (/docs/python-reference/packages/phlo-pandera/phlo_pandera/partitioning)



Partition scoping utilities for SQL quality checks.

This module provides utilities for applying partition-based scoping to SQL queries
used in quality checks. It supports:

1. **Explicit partition keys**: Apply partition filter when partition key is known
2. **Rolling windows**: Apply date range filter for recent data
3. **Full table scans**: Option to disable partitioning for historical analysis

The partition scoping integrates with Dagster's partition mechanism, automatically
applying the correct filters based on the execution context.

Example:

```python
from phlo_pandera.partitioning import PartitionScope, apply_partition_scope

# Scope to specific partition
scope = PartitionScope(
    partition_key="2024-01-15",
    partition_column="_phlo_partition_date",
    rolling_window_days=None,
    full_table=False,
)
sql = apply_partition_scope("SELECT * FROM events", scope=scope)
# Result: SELECT * FROM events
WHERE _phlo_partition_date = DATE '2024-01-15'

# Rolling window (last 7 days)
scope = PartitionScope(
    partition_key=None,
    partition_column="event_date",
    rolling_window_days=7,
    full_table=False,
)
sql = apply_partition_scope("SELECT * FROM events", scope=scope)
# Result includes: WHERE event_date >= DATE 'YYYY-MM-DD'

# Full table scan (no partition filtering)
scope = PartitionScope(
    partition_key=None,
    partition_column="_phlo_partition_date",
    rolling_window_days=None,
    full_table=True,
)
sql = apply_partition_scope("SELECT * FROM events", scope=scope)
# Result: SELECT * FROM events (unchanged)
```

See Also:

* `decorator.py`: Uses partition scoping in `@phlo_pandera`
* `checks.py`: Quality checks that operate on partitioned data

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PartitionScope&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/partitioning/PartitionScope&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_partition_key&#x22;" type="&#x22;(context) -> str | None&#x22;">
      Extract a partition key from a Dagster-like execution context.

      Attempts to retrieve the partition key from standard context attributes:

      1. `context.partition_key`
      2. `context.asset_partition_key`

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        # In a Dagster asset
        from dagster import OpExecutionContext

        @asset(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))
        def my_asset(context: OpExecutionContext):
            partition_key = get_partition_key(context)
            # Returns: "2024-01-15" (for example)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_partition_key(context: object) -> str | None:
            """Extract a partition key from a Dagster-like execution context.

            Attempts to retrieve the partition key from standard context attributes:
            1. ``context.partition_key``
            2. ``context.asset_partition_key``

            Args:
                context: Context object exposing partition key attributes, typically
                    a Dagster OpExecutionContext or similar.

            Returns:
                Partition key value when available (typically YYYY-MM-DD format),
                otherwise None.

            Example:
                \```python
                # In a Dagster asset
                from dagster import OpExecutionContext

                @asset(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))
                def my_asset(context: OpExecutionContext):
                    partition_key = get_partition_key(context)
                    # Returns: "2024-01-15" (for example)
                \```

            """

            partition_key = getattr(context, "partition_key", None)
            if isinstance(partition_key, str) and partition_key:
                return partition_key

            asset_partition_key = getattr(context, "asset_partition_key", None)
            if isinstance(asset_partition_key, str) and asset_partition_key:
                return asset_partition_key

            return None
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;object&#x22;" value="undefined">
          Context object exposing partition key attributes, typically
          a Dagster OpExecutionContext or similar.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        Partition key value when available (typically YYYY-MM-DD format),
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;apply_partition_scope&#x22;" type="&#x22;(sql, *, scope) -> str&#x22;">
      Apply partition scope predicates to a SQL statement.

      Appends WHERE clauses to a SQL query based on the partition scope
      configuration. Handles both explicit partition keys and rolling windows.

      Args:
      sql: Base SQL statement to scope. Should be a SELECT query.
      scope: Partition filtering configuration defining the scope rules.

      Returns:
      SQL statement with appended partition predicates when required.
      Returns the original SQL if scope.full\_table is True or no scoping
      rules are configured.

      Example:

      ```python
      # Apply specific partition filter
      scope = PartitionScope(
          partition_key="2024-01-15",
          partition_column="_phlo_partition_date",
          rolling_window_days=None,
          full_table=False,
      )
      result = apply_partition_scope("SELECT * FROM events", scope=scope)
      # Returns: SELECT * FROM events
      WHERE _phlo_partition_date = DATE '2024-01-15'

      # Apply rolling window
      scope = PartitionScope(
          partition_key=None,
          partition_column="event_date",
          rolling_window_days=30,
          full_table=False,
      )
      result = apply_partition_scope("SELECT * FROM events", scope=scope)
      # Returns query with: WHERE event_date >= DATE 'YYYY-MM-DD' (30 days ago)
      ```

      <PySourceCode>
        ````python
        def apply_partition_scope(sql: str, *, scope: PartitionScope) -> str:
            """Apply partition scope predicates to a SQL statement.

            Appends WHERE clauses to a SQL query based on the partition scope
            configuration. Handles both explicit partition keys and rolling windows.

            Args:
                sql: Base SQL statement to scope. Should be a SELECT query.
                scope: Partition filtering configuration defining the scope rules.

            Returns:
                SQL statement with appended partition predicates when required.
                Returns the original SQL if scope.full_table is True or no scoping
                rules are configured.

            Example:
                \```python
                # Apply specific partition filter
                scope = PartitionScope(
                    partition_key="2024-01-15",
                    partition_column="_phlo_partition_date",
                    rolling_window_days=None,
                    full_table=False,
                )
                result = apply_partition_scope("SELECT * FROM events", scope=scope)
                # Returns: SELECT * FROM events\nWHERE _phlo_partition_date = DATE '2024-01-15'

                # Apply rolling window
                scope = PartitionScope(
                    partition_key=None,
                    partition_column="event_date",
                    rolling_window_days=30,
                    full_table=False,
                )
                result = apply_partition_scope("SELECT * FROM events", scope=scope)
                # Returns query with: WHERE event_date >= DATE 'YYYY-MM-DD' (30 days ago)
                \```

            """

            if scope.full_table:
                return sql

            if scope.partition_key is not None:
                return _append_where(
                    sql, f"{scope.partition_column} = {_date_literal(scope.partition_key)}"
                )

            if scope.rolling_window_days is None:
                return sql

            cutoff = date.today() - timedelta(days=scope.rolling_window_days)
            return _append_where(sql, f"{scope.partition_column} >= {_date_literal(cutoff.isoformat())}")
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;scope&#x22;" type="&#x22;PartitionScope&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_date_literal&#x22;" type="&#x22;(value) -> str&#x22;">
      Format a SQL date literal.

      Converts an ISO date string to a SQL DATE literal expression.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        _date_literal("2024-01-15")
        # Returns: "DATE '2024-01-15'"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _date_literal(value: str) -> str:
            """Format a SQL date literal.

            Converts an ISO date string to a SQL DATE literal expression.

            Args:
                value: ISO date string (YYYY-MM-DD format).

            Returns:
                SQL date literal expression (e.g., "DATE '2024-01-15'").

            Example:
                \```python
                _date_literal("2024-01-15")
                # Returns: "DATE '2024-01-15'"
                \```

            """

            return f"DATE '{value}'"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
          ISO date string (YYYY-MM-DD format).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        SQL date literal expression (e.g., "DATE '2024-01-15'").
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_append_where&#x22;" type="&#x22;(sql, condition) -> str&#x22;">
      Append a condition to SQL with WHERE or AND.

      Intelligently appends a predicate to a SQL query. If the query already
      contains a WHERE clause, the condition is appended with AND. Otherwise,
      a new WHERE clause is added.

      Args:
      sql: Base SQL statement (typically a SELECT query).
      condition: SQL predicate expression to append.

      Returns:
      SQL statement with the condition properly appended.

      Example:

      ```python
      # Query without WHERE
      _append_where("SELECT * FROM events", "id > 100")
      # Returns: SELECT * FROM events
      WHERE id > 100

      # Query with existing WHERE
      _append_where("SELECT * FROM events WHERE status = 'active'", "id > 100")
      # Returns: SELECT * FROM events WHERE status = 'active'
      AND id > 100
      ```

      <PySourceCode>
        ````python
        def _append_where(sql: str, condition: str) -> str:
            """Append a condition to SQL with WHERE or AND.

            Intelligently appends a predicate to a SQL query. If the query already
            contains a WHERE clause, the condition is appended with AND. Otherwise,
            a new WHERE clause is added.

            Args:
                sql: Base SQL statement (typically a SELECT query).
                condition: SQL predicate expression to append.

            Returns:
                SQL statement with the condition properly appended.

            Example:
                \```python
                # Query without WHERE
                _append_where("SELECT * FROM events", "id > 100")
                # Returns: SELECT * FROM events\nWHERE id > 100

                # Query with existing WHERE
                _append_where("SELECT * FROM events WHERE status = 'active'", "id > 100")
                # Returns: SELECT * FROM events WHERE status = 'active'\nAND id > 100
                \```

            """

            if "where" in sql.lower():
                return f"{sql}\nAND {condition}"
            return f"{sql}\nWHERE {condition}"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;sql&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;condition&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
