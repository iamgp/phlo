# Marquez (OpenLineage & Data Lineage)

## Overview

Marquez is an open-source metadata service that implements the OpenLineage standard. It captures, stores, and visualizes end-to-end data lineage across all pipeline components.

## Access

**API**: http://localhost:5555
**Web UI**: http://localhost:3002

## Architecture

### Containers
- **marquez**: API server (port 5000/5555)
- **marquez-web**: React web UI (port 3002)

### Database
Uses Postgres for metadata storage:
- **Database**: `marquez`
- **Schema**: Internal Marquez tables
- **User**: `marquez` / `marquez`

## OpenLineage Integration

### What is OpenLineage?
Industry standard for data lineage:
- **Lineage events**: Emitted by tools (dbt, Dagster, Airflow)
- **Namespace**: Logical grouping (e.g., `lakehouse`)
- **Datasets**: Tables, files, topics
- **Jobs**: Transformations and pipelines
- **Runs**: Individual job executions

### Configured Integrations

#### 1. dbt
Configured in `dagster/assets/dbt_assets.py`:
```python
openlineage_env = {
    "OPENLINEAGE_URL": "http://marquez:5000",
    "OPENLINEAGE_NAMESPACE": "lakehouse",
    "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
}
```

dbt automatically emits:
- **Datasets**: All dbt models as datasets
- **Jobs**: Each dbt run
- **Lineage**: Model dependencies (ref relationships)

#### 2. Dagster
Configured in `dagster/repository.py`:
```python
resources={
    "openlineage": OpenLineageResource(
        url="http://marquez:5000",
        namespace="lakehouse"
    ),
}
```

Dagster emits:
- **Datasets**: Dagster assets
- **Jobs**: Asset materializations
- **Lineage**: Asset dependencies

## Viewing Lineage

### Web UI
1. Navigate to http://localhost:3002
2. Select namespace: `lakehouse`
3. Browse:
   - **Datasets**: All tables/files
   - **Jobs**: All transformations
   - **Lineage Graph**: Visual lineage

### Example Lineage Flow
```
Dataset: raw_bioreactor_data
    ↓
Job: dbt_staging_models
    ↓
Dataset: stg_bioreactor
    ↓
Job: dbt_curated_models
    ↓
Dataset: dim_batch, fact_bioreactor_batch_stats
    ↓
Job: dbt_postgres_marts
    ↓
Dataset: mart_bioreactor_overview
    ↓
Consumer: Superset
```

## API Usage

### List Namespaces
```bash
curl http://localhost:5555/api/v1/namespaces
```

### List Datasets
```bash
curl http://localhost:5555/api/v1/namespaces/lakehouse/datasets
```

### Get Dataset Lineage
```bash
curl http://localhost:5555/api/v1/lineage?nodeId=dataset:lakehouse:mart_bioreactor_overview
```

### List Jobs
```bash
curl http://localhost:5555/api/v1/namespaces/lakehouse/jobs
```

## Emitting Custom Events

### Python OpenLineage Client
```python
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.facet import SqlJobFacet

client = OpenLineageClient(url="http://marquez:5000")

# Create run event
event = RunEvent(
    eventType=RunState.COMPLETE,
    eventTime="2025-01-15T10:00:00Z",
    run=Run(runId="custom-run-123"),
    job=Job(
        namespace="lakehouse",
        name="custom_etl_job",
        facets={"sql": SqlJobFacet(query="SELECT * FROM source")}
    ),
    inputs=[{"namespace": "lakehouse", "name": "raw_data"}],
    outputs=[{"namespace": "lakehouse", "name": "processed_data"}]
)

client.emit(event)
```

### Using Dagster OpenLineage Resource
```python
from dagster import asset

@asset
def custom_asset(context, openlineage: OpenLineageResource):
    # Your processing logic
    result = process_data()

    # Emit custom lineage event
    openlineage.emit_event({
        "job": {"namespace": "lakehouse", "name": "custom_asset"},
        "inputs": [{"namespace": "lakehouse", "name": "input_dataset"}],
        "outputs": [{"namespace": "lakehouse", "name": "output_dataset"}]
    })

    return result
```

## Lineage Use Cases

### 1. Impact Analysis
**Question**: What will break if I change `stg_bioreactor`?

**Answer**: View downstream lineage in Marquez UI:
- `int_bioreactor_downsample_5m`
- `dim_batch`
- `fact_bioreactor_batch_stats`
- `mart_bioreactor_overview`
- All Superset dashboards using these

### 2. Root Cause Analysis
**Question**: Why is `mart_bioreactor_overview` showing wrong data?

**Answer**: Trace upstream lineage:
1. Check `fact_bioreactor_batch_stats` in DuckDB
2. Verify `dim_batch` quality
3. Inspect `stg_bioreactor` for issues
4. Check raw parquet files

### 3. Data Discovery
**Question**: Where does batch_id come from?

**Answer**: Search "batch_id" in Marquez:
- **Source**: `raw_bioreactor_data` parquet files
- **First usage**: `stg_bioreactor` model
- **Transformations**: Used as join key in curated layer
- **Final destination**: `mart_bioreactor_overview`

### 4. Compliance & Auditing
**Question**: Show data lineage for audit?

**Answer**: Export lineage graph from Marquez:
- Full path from source to dashboard
- Transformations applied
- Data quality checks
- Execution timestamps

## Data Retention

### Configure Retention
Marquez doesn't auto-delete old data. Configure cleanup:

```sql
-- In marquez database
DELETE FROM runs
WHERE created_at < CURRENT_DATE - INTERVAL '90 days';

DELETE FROM job_versions
WHERE created_at < CURRENT_DATE - INTERVAL '180 days';
```

Add to cron or scheduled dbt job.

## Monitoring

### Health Check
```bash
curl http://localhost:5555/api/v1/namespaces
# Should return 200 OK with namespaces
```

### Container Logs
```bash
docker compose logs marquez -f
docker compose logs marquez-web -f
```

### Database Size
```sql
-- Connect to marquez db
docker compose exec postgres psql -U marquez -d marquez

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Advanced Features

### Column-Level Lineage
Track individual column transformations:
```python
# In dbt model
{{ config(
    column_lineage=true
) }}

SELECT
  batch_id,  -- FROM raw_bioreactor_data.batch_id
  avg(value) as avg_value  -- COMPUTED FROM raw_bioreactor_data.value
FROM {{ ref('stg_bioreactor') }}
```

Marquez will track:
- `mart_bioreactor_overview.avg_value` ← `stg_bioreactor.value` ← `raw_parquet.value`

### Data Quality Facets
Attach quality metrics to lineage:
```python
from openlineage.client.facet import DataQualityMetricsFacet

event = RunEvent(
    # ... other fields
    outputs=[{
        "namespace": "lakehouse",
        "name": "mart_bioreactor_overview",
        "facets": {
            "dataQuality": DataQualityMetricsFacet(
                rowCount=1000,
                bytes=52428800,
                columnMetrics={
                    "avg_value": {
                        "nullCount": 0,
                        "min": 0.1,
                        "max": 100.5
                    }
                }
            )
        }
    }]
)
```

### Schema Evolution
Marquez tracks schema changes over time:
- Added/removed columns
- Type changes
- Constraint modifications

View in UI: Dataset → Schema tab → History

## Troubleshooting

### Events Not Appearing
1. Check Marquez is running:
   ```bash
   docker compose ps marquez
   ```

2. Verify OpenLineage URL:
   ```bash
   docker compose exec dagster-web env | grep OPENLINEAGE
   ```

3. Check Marquez logs for errors:
   ```bash
   docker compose logs marquez | grep ERROR
   ```

### Lineage Graph Not Loading
1. Clear browser cache
2. Check marquez-web logs:
   ```bash
   docker compose logs marquez-web
   ```

3. Verify API accessibility:
   ```bash
   curl http://localhost:5555/api/v1/namespaces/lakehouse/datasets
   ```

### Duplicate Jobs/Datasets
Caused by namespace/naming inconsistency. Ensure:
- Same namespace everywhere: `lakehouse`
- Consistent naming (e.g., schema.table format)

## Integration with Other Tools

### Great Expectations
Emit data quality results to Marquez:
```python
from openlineage.client import OpenLineageClient

# After GE validation
client = OpenLineageClient(url="http://marquez:5000")
client.emit({
    "job": {"namespace": "lakehouse", "name": "ge_validation"},
    "outputs": [{
        "namespace": "lakehouse",
        "name": "stg_bioreactor",
        "facets": {
            "dataQuality": {
                "validationsPassed": 10,
                "validationsFailed": 0
            }
        }
    }]
})
```

### Airbyte (when configured)
Airbyte natively supports OpenLineage. Configure in Airbyte UI:
1. Settings → OpenLineage
2. Enter: `http://marquez:5000`
3. Namespace: `lakehouse`

Airbyte will emit:
- Source datasets
- Destination datasets (MinIO/S3)
- Sync jobs

## Best Practices

1. **Consistent Namespaces**: Use `lakehouse` everywhere
2. **Descriptive Names**: Use schema.table format for datasets
3. **Emit on Every Run**: Don't skip lineage events
4. **Include Metadata**: Add custom facets for context
5. **Column Lineage**: Enable for critical fields
6. **Retention Policy**: Clean old data periodically
7. **Documentation**: Link Marquez lineage in Confluence/wiki

## Next Steps

- [OpenLineage + Dagster](../integrations/dagster-openlineage.md)
- [OpenLineage + dbt](../integrations/dbt-openlineage.md)
- [Lineage Best Practices](../guides/lineage-best-practices.md)
