# executor (/docs/python-reference/packages/phlo-dlt/phlo_dlt/executor)



DLT ingestion executor implementation.

This module provides the DltIngester class, which implements the full ingestion
pipeline from DLT extraction through Parquet staging to table store loading.
It orchestrates the helpers from :mod:`phlo_dlt.dlt_helpers` and validation
from :mod:`phlo_dlt.pandera_checks` to execute complete ingestion runs.

The executor follows the Write-Audit-Publish (WAP) pattern when strict
validation is enabled, writing to isolated branches for validation before
promotion to the main branch.

Key Class:

* :class:`DltIngester`: Main ingestion executor implementing BaseIngester

Execution Flow:

1. Setup DLT pipeline for extraction
2. Stage data to Parquet files
3. Inject metadata columns (\_phlo\_row\_id, etc.)
4. Validate against Pandera schema (if configured)
5. Merge to table store (append or upsert)
6. Emit telemetry and return results

Hook Integration:
The executor integrates with Phlo's hook system for event emission:

* IngestionEventEmitter: Lifecycle events (start, end)
* TelemetryEventEmitter: Metrics and logs

See Also:

* :class:`phlo.operations.ingestion.BaseIngester`: Abstract base class
* :mod:`phlo_dlt.dlt_helpers`: Helper functions used by executor
* :mod:`phlo_dlt.pandera_checks`: Validation integration
* :mod:`phlo.hooks`: Event emission system

Example:

```python
from phlo_dlt.executor import DltIngester
from phlo_dlt.registry import TableConfig

ingester = DltIngester(
    context=dagster_context,
    logger=logger,
    table_config=table_config,
    table_store_resource=iceberg_store,
    dlt_source_func=fetch_users,
    validation_schema=UserSchema,
    validate=True,
    strict_validation=True,
)
result = ingester.run_ingestion(
    partition_key="2024-01-01",
    parameters=\{"branch_name": "main", "run_id": "run-123"\}
)
```

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DltIngester&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/executor/DltIngester&#x22;" />
    </Cards>
  </Tab>
</Tabs>
