# Dagster (Orchestration & Asset Management)

## Overview

Dagster orchestrates the entire data pipeline using an **asset-based** architecture. Each data transformation, table, and file is represented as an asset with explicit dependencies and lineage.

## Architecture

### Containers
- **dagster-webserver**: Web UI and GraphQL API (port 3000)
- **dagster-daemon**: Background scheduler and sensor executor

### Asset-Based Design
Unlike traditional job-based orchestrators, Dagster models:
- **What** you're building (assets)
- **How** they depend on each other (lineage)
- **When** they should refresh (schedules, sensors)

## Assets

### Raw Layer
**`raw_bioreactor_data`**
- **Type**: Python asset
- **Purpose**: Monitor raw parquet files
- **Location**: `/data/lake/raw/bioreactor/*.parquet`
- **Output**: File count and availability status
- **Trigger**: Manual or sensor-based

### dbt Layer
**`dbt_staging_models`**
- **Type**: dbt asset
- **Purpose**: Clean and standardize raw data
- **Models**: `stg_bioreactor` (tagged `stg`)
- **Target**: DuckDB views
- **Depends on**: `raw_bioreactor_data`

**`dbt_curated_models`**
- **Type**: dbt asset
- **Purpose**: Apply business logic and aggregations
- **Models**:
  - `int_bioreactor_downsample_5m` (tag: `int`)
  - `dim_batch`, `fact_bioreactor_batch_stats` (tag: `curated`)
- **Target**: DuckDB tables
- **Depends on**: `dbt_staging_models`

**`dbt_postgres_marts`**
- **Type**: dbt asset
- **Purpose**: Analytics-ready tables for BI
- **Models**: `mart_bioreactor_overview` (tag: `mart`)
- **Target**: Postgres marts schema
- **Depends on**: `dbt_curated_models`

## Asset Graph Visualization

```
raw_bioreactor_data
        ↓
dbt_staging_models (DuckDB views)
        ↓
dbt_curated_models (DuckDB tables)
        ↓
dbt_postgres_marts (Postgres tables)
        ↓
    Superset
```

View in UI: http://localhost:3000 → Assets → "View asset graph"

## Jobs

### `ingest_raw_data`
- **Selection**: `AssetSelection.groups("raw_ingestion")`
- **Assets**: `raw_bioreactor_data`
- **Purpose**: Validate raw data availability
- **Trigger**: Manual or sensor

### `transform_dbt_models`
- **Selection**: `AssetSelection.all()`
- **Assets**: All dbt assets (staging → curated → marts)
- **Purpose**: Run full transformation pipeline
- **Trigger**: Manual, schedule, or after ingestion

## Schedules

### `nightly_pipeline`
- **Job**: `transform_dbt_models`
- **Cron**: `0 2 * * *` (2 AM London time)
- **Timezone**: `Europe/London`
- **Status**: Check in UI → Automation → Schedules

### Managing Schedules
```bash
# Enable/disable in UI or via CLI
docker compose exec dagster-web dagster schedule list
docker compose exec dagster-web dagster schedule start nightly_pipeline
docker compose exec dagster-web dagster schedule stop nightly_pipeline
```

## Resources

### dbt
```python
DbtCliResource(
    project_dir="/dbt",
    profiles_dir="/dbt/profiles",
)
```

### Airbyte (optional)
```python
AirbyteResource(
    host=os.getenv("AIRBYTE_HOST", "localhost"),
    port=os.getenv("AIRBYTE_API_PORT", "8001"),
)
```

### OpenLineage
```python
OpenLineageResource(
    url="http://marquez:5000",
    namespace="lakehouse"
)
```

## Materialization

### Via UI
1. Navigate to http://localhost:3000
2. Go to "Assets"
3. Select asset(s)
4. Click "Materialize"

### Via CLI
```bash
# Materialize all assets
docker compose exec dagster-web dagster asset materialize --select '*'

# Materialize specific asset
docker compose exec dagster-web dagster asset materialize --select dbt_staging_models

# Materialize asset group
docker compose exec dagster-web dagster asset materialize --select 'group:dbt_curated'

# Materialize with dependencies
docker compose exec dagster-web dagster asset materialize --select '+dbt_postgres_marts'
```

### Programmatic (Python)
```python
from dagster import materialize
from repository import dbt_staging_models, dbt_curated_models

# Materialize assets
result = materialize([dbt_staging_models, dbt_curated_models])
```

## Sensors (Future Enhancement)

Add sensors to trigger on events:

### File Arrival Sensor
```python
from dagster import sensor, RunRequest

@sensor(job=transform_job)
def raw_file_sensor(context):
    """Trigger when new parquet files arrive"""
    files = check_for_new_files('/data/lake/raw/bioreactor/')
    if files:
        return RunRequest(
            run_config={"ops": {"assets": {"config": {"files": files}}}}
        )
```

### S3 Sensor
```python
from dagster_aws.s3 import s3_resource

@sensor(job=transform_job)
def s3_sensor(context):
    """Trigger on MinIO/S3 uploads"""
    # Implementation
```

## Partitions (Future Enhancement)

Partition assets by batch or date:

```python
from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(start_date="2025-01-01")

@asset(partitions_def=daily_partition)
def dbt_staging_models(context):
    partition_date = context.partition_key
    # Run dbt for specific partition
```

## Asset Checks (Data Quality)

Add Great Expectations as asset checks:

```python
from dagster import asset_check, AssetCheckResult

@asset_check(asset=dbt_staging_models)
def validate_staging_data(context):
    """Run Great Expectations validation"""
    result = run_ge_checkpoint("staging_checkpoint")
    return AssetCheckResult(
        passed=result.success,
        metadata={"validation_results": result.to_json()}
    )
```

## Monitoring & Observability

### Asset Catalog
- **URL**: http://localhost:3000/assets
- **Shows**: All assets, last materialization, status
- **Metadata**: Row counts, execution time, custom metadata

### Run History
- **URL**: http://localhost:3000/runs
- **Filters**: By job, asset, status, date range
- **Details**: Logs, compute logs, structured metadata

### Logs
```bash
# Web server logs
docker compose logs dagster-webserver -f

# Daemon logs (schedules, sensors)
docker compose logs dagster-daemon -f

# Specific run logs
# View in UI: Runs → Select run → Logs tab
```

### OpenLineage Integration
Dagster emits lineage events to Marquez:
- **Marquez API**: http://localhost:5555
- **Marquez UI**: http://localhost:3002
- **Namespace**: `lakehouse`

## Configuration

### Environment Variables
Set in `docker-compose.yml`:
```yaml
DAGSTER_HOME: /opt/dagster
DBT_PROFILES_DIR: /dbt/profiles
OPENLINEAGE_URL: http://marquez:5000
OPENLINEAGE_NAMESPACE: lakehouse
AWS_ACCESS_KEY_ID: ${MINIO_ROOT_USER}
AWS_SECRET_ACCESS_KEY: ${MINIO_ROOT_PASSWORD}
AWS_S3_ENDPOINT: http://minio:9000
```

### dagster.yaml
Location: `/opt/dagster/dagster.yaml`
```yaml
run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher

run_storage:
  module: dagster.core.storage.runs
  class: SqliteRunStorage
  config:
    base_dir: /opt/dagster/history

event_log_storage:
  module: dagster.core.storage.event_log
  class: SqliteEventLogStorage
  config:
    base_dir: /opt/dagster/history
```

## Development Workflow

### 1. Local Development
Edit assets in `dagster/assets/`:
```python
# dagster/assets/dbt_assets.py
@asset(group_name="dbt_staging")
def dbt_staging_models(context, dbt):
    # Your logic here
```

### 2. Reload Definitions
Changes auto-reload in development. Force reload:
```bash
docker compose restart dagster-webserver dagster-daemon
```

### 3. Test Assets
```python
# In Python
from dagster import build_asset_context
from assets.dbt_assets import dbt_staging_models

context = build_asset_context()
result = dbt_staging_models(context)
```

### 4. View in UI
Navigate to http://localhost:3000/assets to see updated lineage

## Backfills

Run historical materializations:

```bash
# Backfill specific date range (with partitions)
docker compose exec dagster-web dagster asset backfill \
  --partitions '2025-01-01:2025-01-31' \
  --select dbt_staging_models

# Backfill all dependencies
docker compose exec dagster-web dagster asset backfill \
  --select '+dbt_postgres_marts'
```

## Troubleshooting

### Assets Not Showing
```bash
# Check repository loaded
docker compose logs dagster-webserver | grep -i "Started Dagster code server"

# Verify workspace
docker compose exec dagster-web cat /opt/dagster/workspace.yaml

# Reload repository
docker compose restart dagster-webserver
```

### Materialization Fails
1. Check run logs in UI
2. View asset logs:
   ```bash
   docker compose logs dagster-webserver | grep "dbt_staging_models"
   ```
3. Test dbt directly:
   ```bash
   docker compose exec dagster-web dbt run --select tag:stg
   ```

### Schedule Not Running
```bash
# Check daemon is running
docker compose ps dagster-daemon

# View daemon logs
docker compose logs dagster-daemon

# Manually trigger
docker compose exec dagster-web dagster schedule tick nightly_pipeline
```

### Permission Issues
```bash
# Fix file permissions
docker compose exec dagster-web chmod -R 777 /data/duckdb
```

## Best Practices

1. **Asset Groups**: Organize related assets into groups
2. **Descriptions**: Add clear descriptions to all assets
3. **Metadata**: Log row counts, execution times as metadata
4. **Checks**: Add data quality checks as asset checks
5. **Partitions**: Use partitions for incremental processing
6. **Sensors**: Automate triggers with sensors
7. **Monitoring**: Set up alerts via Dagster Cloud or custom webhooks

## Next Steps

See integration docs for:
- [Dagster + dbt Integration](../integrations/dagster-dbt.md)
- [Dagster + OpenLineage](../integrations/dagster-openlineage.md)
- [Dagster + Airbyte](../integrations/dagster-airbyte.md)
