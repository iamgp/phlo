# Asset-Based Data Lakehouse Architecture

## Overview

The lakehouse platform has been migrated from job-based orchestration to Dagster's modern **asset-based architecture**. This provides clear data lineage, better observability, and a visual asset catalog.

## What Changed

### Before (Job-Based)
- 3 independent jobs without clear dependencies
- No visibility into data lineage
- Manual coordination between ingestion → transformation → validation

### After (Asset-Based)
- **4 core assets** with explicit dependencies
- Visual lineage graph in Dagster UI
- Automatic dependency resolution and scheduling

## Asset Graph

```
raw_bioreactor_data
        |
        v
dbt_staging_models (stg_bioreactor)
        |
        v
dbt_curated_models (int_*, dim_*, fact_*)
        |
        v
dbt_postgres_marts (mart_*)
```

## Assets Explained

### 1. `raw_bioreactor_data`
- **Group**: `raw_ingestion`
- **Purpose**: Represents raw parquet files from data sources
- **Location**: `/data/lake/raw/bioreactor/*.parquet`
- **Upstream**: Airbyte connections (when configured) or manual file drops
- **Output**: File count and status metadata

### 2. `dbt_staging_models`
- **Group**: `dbt_staging`
- **Purpose**: Clean and standardize raw data
- **dbt models**: `stg_bioreactor` (tagged `stg`)
- **Target**: DuckDB views
- **Upstream**: `raw_bioreactor_data`

### 3. `dbt_curated_models`
- **Group**: `dbt_curated`
- **Purpose**: Business logic, aggregations, and enrichments
- **dbt models**:
  - `int_bioreactor_downsample_5m` (intermediate, tagged `int`)
  - `dim_batch`, `fact_bioreactor_batch_stats` (curated, tagged `curated`)
- **Target**: DuckDB tables
- **Upstream**: `dbt_staging_models`

### 4. `dbt_postgres_marts`
- **Group**: `dbt_marts`
- **Purpose**: Analytics-ready tables for BI/dashboards
- **dbt models**: `mart_bioreactor_overview` (tagged `mart`)
- **Target**: PostgreSQL
- **Upstream**: `dbt_curated_models`
- **Consumers**: Superset dashboards

## Jobs

### `ingest_raw_data`
Materializes assets in the `raw_ingestion` group
- Triggers Airbyte syncs (when configured)
- Validates raw data presence

### `transform_dbt_models`
Materializes the full dbt pipeline
- Runs all dbt assets in dependency order
- Ensures data flows from staging → curated → marts

## Schedules

### `nightly_pipeline`
- **Job**: `transform_dbt_models`
- **Cron**: `0 2 * * *` (02:00 AM London time)
- **Purpose**: Daily automated refresh of all analytics

## Airbyte Integration

Airbyte is configured but optional. See [AIRBYTE_SETUP.md](./AIRBYTE_SETUP.md) for instructions.

When Airbyte is running:
1. Dagster will load each Airbyte connection as an asset
2. Materializing those assets triggers data syncs
3. Downstream dbt assets automatically run after ingestion completes

## Benefits of Asset-Based Approach

### 1. **Lineage Visibility**
- See exactly how data flows through your pipeline
- Track which assets are upstream/downstream
- Understand impact of changes

### 2. **Selective Materialization**
- Materialize individual assets or asset groups
- Only run what changed (incremental processing)
- Save compute resources

### 3. **Better Observability**
- Track when each asset was last materialized
- See materialization history and durations
- Monitor data freshness

### 4. **Easier Debugging**
- Identify exactly which asset failed
- Re-run only failed assets
- View logs per asset

### 5. **Automatic Backfills**
- Dagster handles backfilling dependencies
- Partition-aware scheduling (future enhancement)
- Data quality checks per asset

## How to Use

### View Assets
1. Open http://localhost:3000
2. Navigate to "Assets" tab
3. See the full asset graph with lineage

### Materialize Assets
**Full pipeline:**
```bash
# Via UI: Click "Materialize All" on transform_dbt_models job
# Via CLI (in container):
dagster asset materialize --select '*'
```

**Individual asset:**
```bash
# Via UI: Click asset → "Materialize"
# Via CLI:
dagster asset materialize --select dbt_staging_models
```

**Asset group:**
```bash
dagster asset materialize --select 'group:dbt_curated'
```

### Monitor Progress
- **Asset Catalog**: Shows materialization status
- **Run History**: View past materializations
- **Logs**: Per-asset execution logs
- **OpenLineage**: Full lineage in Marquez at http://localhost:5555

## Next Steps

### Recommended Enhancements

1. **Add Sensors**
   - Trigger `dbt_staging_models` when new parquet files arrive
   - Watch S3/MinIO for new data

2. **Partition Assets**
   - Partition by batch_id or date
   - Enable incremental processing

3. **Data Quality Checks**
   - Add Great Expectations as asset checks
   - Fail materialization if quality thresholds not met

4. **Add More Sources**
   - Configure Airbyte connections for LIMS, ELN, etc.
   - Each connection becomes a separate asset

5. **Metadata Logging**
   - Add row counts, data ranges to asset metadata
   - Track data volume over time

## File Structure

```
dagster/
├── assets/
│   ├── __init__.py
│   ├── airbyte_assets.py      # Airbyte connection assets
│   ├── dbt_assets.py           # dbt model assets (staging, curated, marts)
│   └── raw_data_assets.py      # Raw file validation assets
├── repository_new.py           # Main definitions with asset-based config
├── workspace.yaml              # Points to repository_new.py
└── ...
```

## URLs

- **Dagster UI**: http://localhost:3000
- **Superset**: http://localhost:8088 (admin/admin123)
- **Marquez (Lineage)**: http://localhost:5555
- **Marquez Web UI**: http://localhost:3002
- **MinIO Console**: http://localhost:9001 (minio/minio999)
