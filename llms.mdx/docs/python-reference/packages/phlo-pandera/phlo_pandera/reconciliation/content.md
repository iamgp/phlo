# reconciliation (/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation)



Reconciliation quality checks for cross-table data validation.

This module provides quality checks that validate data consistency across
different tables or data layers. These checks are essential for ensuring
data integrity in ETL/ELT pipelines where data flows through multiple stages
(raw -> bronze -> silver -> gold).

Reconciliation checks compare data between a source table (earlier in the
pipeline) and a target table (later in the pipeline) to detect:

* Data loss during transformation
* Unexpected row count changes
* Aggregate computation errors
* Key mismatches
* Checksum/hash mismatches

Available Reconciliation Checks:

* **ReconciliationCheck**: Compare row counts between source and target tables
* **AggregateConsistencyCheck**: Verify computed aggregates match expectations
* **KeyParityCheck**: Ensure matching keys between source and target tables
* **MultiAggregateConsistencyCheck**: Compare multiple aggregates efficiently
* **ChecksumReconciliationCheck**: Validate row-level data integrity using hashes

Common Use Cases:

1. **ETL Validation**: Ensure no data loss between extraction and load
2. **Transformation Verification**: Confirm aggregates are computed correctly
3. **Data Migration**: Validate data moved correctly between systems
4. **Pipeline Monitoring**: Detect issues early before they propagate downstream

Example:

```python
from phlo_pandera import (
    ReconciliationCheck,
    AggregateConsistencyCheck,
    KeyParityCheck,
    phlo_pandera,
)

@phlo_pandera(
    table="silver.sales_summary",
    checks=[
        # Ensure row count matches source
        ReconciliationCheck(
            source_table="bronze.sales_raw",
            check_type="rowcount_parity",
            tolerance=0.01,  # Allow 1% difference
        ),
        # Verify total_sales aggregate
        AggregateConsistencyCheck(
            source_table="bronze.sales_raw",
            aggregate_column="total_sales",
            source_expression="SUM(amount)",
            tolerance=0.0,  # Exact match required
        ),
        # Ensure all customer_ids are present
        KeyParityCheck(
            source_table="bronze.sales_raw",
            key_columns=["customer_id"],
        ),
    ],
)
def sales_summary_validation():
    pass
```

Partitioning Support:
All reconciliation checks support partition-aware validation using the
default `_phlo_partition_date` column. When running in a partitioned
context, checks automatically scope queries to the current partition.

See Also:

* `checks.py`: Core quality checks for single-table validation
* `checks_extra.py`: Extended checks (SchemaCheck, CustomSQLCheck, PatternCheck)
* `decorator.py`: `@phlo_pandera` for integration

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ReconciliationCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/ReconciliationCheck&#x22;" />

      <Card title="&#x22;AggregateConsistencyCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/AggregateConsistencyCheck&#x22;" />

      <Card title="&#x22;AggregateSpec&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/AggregateSpec&#x22;" />

      <Card title="&#x22;KeyParityCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/KeyParityCheck&#x22;" />

      <Card title="&#x22;MultiAggregateConsistencyCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/MultiAggregateConsistencyCheck&#x22;" />

      <Card title="&#x22;ChecksumReconciliationCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/reconciliation/ChecksumReconciliationCheck&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_get_context_resource&#x22;" type="&#x22;(context, name) -> Any | None&#x22;">
      Fetch a resource from context, supporting attribute and helper access.

      <PySourceCode>
        ```python
        def _get_context_resource(context: RuntimeContext, name: str) -> Any | None:
            """Fetch a resource from context, supporting attribute and helper access.

            Args:
                context: Runtime context that may contain resources.
                name: Name of the resource to fetch (e.g., "trino").

            Returns:
                Resource object if found, None otherwise.

            """
            resources = getattr(context, "resources", None)
            if isinstance(resources, dict):
                resource = resources.get(name)
                if resource is not None:
                    return resource
            elif resources is not None:
                if hasattr(resources, name):
                    resource = getattr(resources, name)
                    if resource is not None:
                        return resource

            try:
                if hasattr(context, "get_resource"):
                    get_resource = getattr(context, "get_resource", None)
                    if get_resource is None:
                        return None
                    if getattr(get_resource, "_spec_class", None) is None and hasattr(
                        get_resource, "mock_calls"
                    ):
                        return None
                    return context.get_resource(name)
            except Exception:
                return None
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context that may contain resources.
        </PyParameter>

        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the resource to fetch (e.g., "trino").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Any | None&#x22;">
        Resource object if found, None otherwise.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
