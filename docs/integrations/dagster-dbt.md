# Dagster + dbt Integration

## Overview

Dagster orchestrates dbt as **assets** rather than jobs, providing:
- Visual lineage of dbt models
- Individual model materialization
- Automatic dependency resolution
- Integration with OpenLineage

## Architecture

### Traditional (Job-Based)
```python
@op
def run_dbt():
    dbt.cli(["run"])

@job
def dbt_job():
    run_dbt()
```
❌ No model visibility
❌ All-or-nothing execution
❌ No lineage graph

### Modern (Asset-Based)
```python
@asset(group_name="dbt_staging")
def dbt_staging_models(context, dbt: DbtCliResource):
    result = dbt.cli(["run", "--select", "tag:stg"], context=context).wait()
    return Output({"success": result.success})
```
✅ Models as assets
✅ Selective execution
✅ Visual lineage

## Implementation

### Current Setup

#### 1. dbt Resource Configuration
`dagster/repository.py`:
```python
resources={
    "dbt": DbtCliResource(
        project_dir="/dbt",
        profiles_dir="/dbt/profiles",
    ),
}
```

#### 2. Asset Definitions
`dagster/assets/dbt_assets.py`:
```python
@asset(group_name="dbt_staging", description="...")
def dbt_staging_models(context, dbt: DbtCliResource):
    openlineage_env = {
        "OPENLINEAGE_URL": "http://marquez:5000",
        "OPENLINEAGE_NAMESPACE": "lakehouse",
    }
    result = dbt.cli(
        ["run", "--select", "tag:stg"],
        context=context,
        env=openlineage_env
    ).wait()
    context.log.info(f"Staging models completed: {result.success}")
    return Output({"success": result.success})
```

#### 3. Asset Dependencies
```python
@asset(deps=[dbt_staging_models])
def dbt_curated_models(context, dbt):
    # Automatically runs after staging
    ...
```

## Benefits

### 1. Model-Level Visibility
**Before**: One "dbt run" job
**After**: Individual assets per layer
- `dbt_staging_models`
- `dbt_curated_models`
- `dbt_postgres_marts`

### 2. Selective Materialization
```bash
# Materialize just staging
dagster asset materialize --select dbt_staging_models

# Materialize staging + downstream
dagster asset materialize --select 'dbt_staging_models+'
```

### 3. Automatic Lineage
Dagster knows:
- `dbt_curated_models` depends on `dbt_staging_models`
- `dbt_postgres_marts` depends on `dbt_curated_models`

View in UI: Assets → View Asset Graph

### 4. OpenLineage Integration
Each dbt run emits lineage events showing:
- Which models ran
- What data they read (inputs)
- What data they wrote (outputs)
- Model-to-model dependencies

## dbt CLI Commands via Dagster

### Available Methods

#### `dbt.cli()`
Execute any dbt command:
```python
# Run all models
dbt.cli(["run"], context=context)

# Run with selection
dbt.cli(["run", "--select", "tag:stg"], context=context)

# Test
dbt.cli(["test", "--select", "stg_bioreactor"], context=context)

# Build (run + test)
dbt.cli(["build", "--select", "tag:curated"], context=context)
```

#### `.wait()` vs `.stream()`
```python
# Wait for completion (blocking)
result = dbt.cli(["run"], context=context).wait()
if result.success:
    context.log.info("dbt run succeeded")

# Stream logs (real-time)
for event in dbt.cli(["run"], context=context).stream():
    context.log.info(event)
```

### Environment Variables
Pass env vars to dbt:
```python
dbt.cli(
    ["run"],
    context=context,
    env={
        "OPENLINEAGE_URL": "http://marquez:5000",
        "DBT_TARGET": "postgres",
    }
)
```

## Multi-Target Pattern

### DuckDB for Transformation
```python
@asset(group_name="dbt_curated")
def dbt_curated_models(context, dbt):
    # Runs against DuckDB (default target)
    result = dbt.cli(
        ["run", "--select", "tag:curated"],
        context=context
    ).wait()
    return Output({"success": result.success})
```

### Postgres for Marts
```python
@asset(group_name="dbt_marts", deps=[dbt_curated_models])
def dbt_postgres_marts(context, dbt):
    # Runs against Postgres (explicit target)
    result = dbt.cli(
        ["run", "--select", "tag:mart", "--target", "postgres"],
        context=context
    ).wait()
    return Output({"success": result.success})
```

dbt automatically reads from DuckDB, writes to Postgres.

## Error Handling

### Check for Failures
```python
@asset
def dbt_staging_models(context, dbt):
    result = dbt.cli(["run", "--select", "tag:stg"], context=context).wait()

    if not result.success:
        raise Exception(f"dbt staging failed: {result.stderr}")

    context.log.info(f"Processed {result.stdout}")
    return Output({"success": True, "output": result.stdout})
```

### Retry Policy
```python
from dagster import RetryPolicy

@asset(retry_policy=RetryPolicy(max_retries=3, delay=60))
def dbt_staging_models(context, dbt):
    # Auto-retries 3 times with 60s delay
    ...
```

### Failure Notifications
```python
from dagster import failure_hook

@failure_hook
def dbt_failure_alert(context):
    send_slack_message(f"dbt asset {context.asset_key} failed")

@asset(op_tags={"hook": dbt_failure_alert})
def dbt_staging_models(context, dbt):
    ...
```

## Testing Integration

### Run dbt Tests as Asset Checks
```python
from dagster import asset_check, AssetCheckResult

@asset_check(asset=dbt_staging_models)
def validate_staging_data(context, dbt):
    result = dbt.cli(["test", "--select", "tag:stg"], context=context).wait()

    return AssetCheckResult(
        passed=result.success,
        metadata={
            "tests_run": result.stdout.count("PASS"),
            "tests_failed": result.stdout.count("FAIL"),
        }
    )
```

Checks run automatically after asset materialization.

## Metadata & Logging

### Add Custom Metadata
```python
@asset
def dbt_curated_models(context, dbt):
    result = dbt.cli(["run", "--select", "tag:curated"], context=context).wait()

    # Parse dbt output for row counts
    models_built = parse_dbt_output(result.stdout)

    return Output(
        value={"success": result.success},
        metadata={
            "models_built": len(models_built),
            "execution_time_seconds": result.duration,
            "models": models_built,
        }
    )
```

View in Dagster UI: Asset → Latest Materialization → Metadata

### Structured Logging
```python
context.log.info(f"Running dbt models with tags: curated")
context.log.debug(f"dbt command: {' '.join(cmd)}")
context.log.warning(f"dbt run took {duration}s (expected <60s)")
context.log.error(f"dbt failed: {result.stderr}")
```

## Advanced Patterns

### Partitioned Assets (Future)
Run dbt incrementally by partition:
```python
from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(start_date="2025-01-01")

@asset(partitions_def=daily_partition)
def dbt_staging_models(context, dbt):
    partition_date = context.partition_key

    result = dbt.cli([
        "run",
        "--select", "tag:stg",
        "--vars", f"{{partition_date: {partition_date}}}"
    ], context=context).wait()

    return Output({"success": result.success})
```

In dbt model:
```sql
{% if var('partition_date', None) %}
  WHERE date(ts) = '{{ var("partition_date") }}'
{% endif %}
```

### Dynamic Asset Selection
Load dbt models dynamically:
```python
from dagster_dbt import load_assets_from_dbt_manifest

dbt_assets = load_assets_from_dbt_manifest(
    manifest_path="/dbt/target/manifest.json",
    select="tag:stg tag:curated",
    exclude="tag:deprecated"
)
```

**Note**: Requires manifest.json generated by `dbt parse`

### Cross-Database Joins
```python
@asset(deps=[dbt_curated_models])
def dbt_postgres_marts(context, dbt):
    # dbt reads from DuckDB, writes to Postgres
    result = dbt.cli([
        "run",
        "--select", "tag:mart",
        "--target", "postgres",
        "--vars", "{'source_db': 'duckdb'}"
    ], context=context).wait()

    return Output({"success": result.success})
```

## Debugging

### View dbt Logs in Dagster
1. Navigate to Dagster UI
2. Go to Run → Select run
3. Click "Compute Logs" tab
4. See full dbt output

### Run dbt Directly
```bash
# Access container
docker compose exec dagster-web bash

# Run dbt manually
cd /dbt
dbt run --select tag:stg --profiles-dir /dbt/profiles
```

### Check Asset Status
```bash
dagster asset list  # Show all assets
dagster asset materialize --select dbt_staging_models --dry-run
```

## Performance Tuning

### Parallel Execution
```python
# In profiles.yml
duckdb:
  type: duckdb
  threads: 8  # Parallel model execution
```

### Incremental Models
```sql
{{ config(
    materialized='incremental',
    unique_key='batch_id'
) }}

SELECT * FROM {{ ref('stg_bioreactor') }}
{% if is_incremental() %}
  WHERE ts > (SELECT max(ts) FROM {{ this }})
{% endif %}
```

### Caching in Dagster
```python
from dagster import mem_io_manager

defs = Definitions(
    assets=[dbt_staging_models],
    resources={
        "dbt": dbt_resource,
        "io_manager": mem_io_manager,  # Cache asset outputs
    }
)
```

## Comparison: Job vs Asset

| Feature | Job-Based | Asset-Based |
|---------|-----------|-------------|
| Visibility | One job | Per-layer assets |
| Lineage | Manual | Automatic |
| Selection | All models | Specific assets |
| Retries | Job-level | Asset-level |
| Monitoring | Job logs | Asset metadata |
| Best For | Simple pipelines | Complex DAGs |

## Migration Guide

### From Jobs to Assets

**Before**:
```python
@op
def run_dbt(dbt: DbtCliResource):
    dbt.cli(["run"])

@job
def dbt_job():
    run_dbt()
```

**After**:
```python
@asset
def dbt_staging_models(context, dbt: DbtCliResource):
    result = dbt.cli(["run", "--select", "tag:stg"], context=context).wait()
    return Output({"success": result.success})
```

### Migration Steps
1. Define dbt layers as assets
2. Add dependencies with `deps=[...]`
3. Update schedules to target asset jobs
4. Remove old job definitions
5. Test in Dagster UI

## Best Practices

1. **One Asset Per Layer**: staging, curated, marts
2. **Use dbt Tags**: Select models with `--select tag:xxx`
3. **OpenLineage**: Always pass OpenLineage env vars
4. **Metadata**: Log row counts, execution time
5. **Error Handling**: Check `result.success` and raise errors
6. **Dependencies**: Use `deps=[]` for cross-asset dependencies
7. **Multi-Target**: Separate transformation (DuckDB) from serving (Postgres)

## Next Steps

- [dbt + DuckDB Patterns](./dbt-duckdb.md)
- [Dagster + OpenLineage](./dagster-openlineage.md)
- [Asset-Based Architecture](../ASSET_BASED_ARCHITECTURE.md)
