# End-to-End Data Flow

## Overview

This document describes how data flows through the entire lakehouse platform, from raw ingestion to final dashboards.

## Complete Flow Diagram

```
┌─────────────┐
│ Data Sources│
│ (LIMS, ELN, │
│ Instruments)│
└──────┬──────┘
       │
       ↓ (Optional: Airbyte)
┌──────────────────┐
│ MinIO / S3       │
│ /raw/bioreactor/ │
│ *.parquet        │
└────────┬─────────┘
         │
         ↓ (Dagster: raw_bioreactor_data asset)
┌────────────────────┐
│ DuckDB - Staging   │
│ stg_bioreactor     │
│ (VIEW)             │
└────────┬───────────┘
         │
         ↓ (Dagster: dbt_staging_models)
┌────────────────────┐
│ DuckDB - Curated   │
│ • dim_batch        │
│ • fact_batch_stats │
│ (TABLES)           │
└────────┬───────────┘
         │
         ↓ (Dagster: dbt_curated_models)
┌────────────────────┐
│ Postgres - Marts   │
│ mart_bioreactor_   │
│ overview           │
└────────┬───────────┘
         │
         ↓ (Dagster: dbt_postgres_marts)
┌────────────────────┐
│ Superset           │
│ Dashboards &       │
│ Reports            │
└────────────────────┘
         │
         ↓ (OpenLineage events)
┌────────────────────┐
│ Marquez            │
│ Full Lineage       │
│ Graph              │
└────────────────────┘
```

## Phase-by-Phase Breakdown

### Phase 1: Ingestion (Optional - Airbyte)

**Trigger**: Scheduled sync or manual
**Tool**: Airbyte (when configured)

1. Airbyte connects to source system (LIMS, instruments)
2. Extracts data via connector
3. Converts to Parquet format
4. Lands in MinIO: `s3://lake/raw/bioreactor/{batch_id}.parquet`
5. Emits OpenLineage event to Marquez

**Alternative**: Manual file drop into `/data/lake/raw/bioreactor/`

### Phase 2: Raw Data Validation

**Trigger**: Dagster sensor (future) or schedule
**Tool**: Dagster asset `raw_bioreactor_data`

1. Checks for parquet files in `/data/lake/raw/bioreactor/`
2. Counts files and validates structure
3. Returns metadata (file count, paths)
4. Marks asset as materialized
5. Emits lineage event

**Output**: Metadata about raw data availability

### Phase 3: Staging (Clean & Standardize)

**Trigger**: Dagster asset `dbt_staging_models`
**Tool**: dbt + DuckDB

1. dbt reads raw parquet via `read_parquet()`
2. Executes `stg_bioreactor.sql`:
   - Type casting (timestamp, varchar, double)
   - Column renaming to snake_case
   - Light cleaning (trim, nullif)
3. Materializes as DuckDB VIEW
4. Emits OpenLineage with input/output lineage

**Output**: `staging.stg_bioreactor` (DuckDB view)

### Phase 4: Curated Layer (Business Logic)

**Trigger**: Dagster asset `dbt_curated_models` (depends on staging)
**Tool**: dbt + DuckDB

1. dbt references `{{ ref('stg_bioreactor') }}`
2. Executes transformations:
   - **Intermediate**: `int_bioreactor_downsample_5m.sql` (time-based aggregation)
   - **Dimensions**: `dim_batch.sql` (batch metadata)
   - **Facts**: `fact_bioreactor_batch_stats.sql` (batch statistics)
3. Materializes as DuckDB TABLES
4. Creates indexes for performance
5. Emits lineage showing model dependencies

**Output**:
- `intermediate.int_bioreactor_downsample_5m`
- `curated.dim_batch`
- `curated.fact_bioreactor_batch_stats`

### Phase 5: Marts (Analytics Tables)

**Trigger**: Dagster asset `dbt_postgres_marts` (depends on curated)
**Tool**: dbt + Postgres

1. dbt switches target to `postgres`
2. Reads from DuckDB curated tables
3. Executes `mart_bioreactor_overview.sql`:
   - Joins dimensions and facts
   - Denormalizes for BI performance
   - Applies final business rules
4. Materializes as Postgres TABLE in `marts` schema
5. Emits lineage showing cross-database flow

**Output**: `marts.mart_bioreactor_overview` (Postgres)

### Phase 6: Visualization

**Trigger**: User access or scheduled report
**Tool**: Superset

1. User opens dashboard
2. Superset queries `marts.mart_bioreactor_overview`
3. Renders charts and filters
4. Caches results (if enabled)
5. Delivers to browser

**Output**: Interactive dashboards

### Phase 7: Lineage Tracking

**Continuous**: All phases
**Tool**: Marquez + OpenLineage

1. Each tool emits OpenLineage events:
   - dbt: Model runs and dependencies
   - Dagster: Asset materializations
   - Airbyte: Data syncs (when configured)
2. Marquez aggregates events
3. Builds lineage graph
4. Exposes via API and UI

**Output**: Complete lineage graph in Marquez UI

## Timing & Scheduling

### Default Schedule
```
02:00 AM - Dagster schedule `nightly_pipeline` triggers
02:00 AM - raw_bioreactor_data validates files
02:01 AM - dbt_staging_models creates views
02:05 AM - dbt_curated_models builds tables
02:10 AM - dbt_postgres_marts updates marts
02:15 AM - Pipeline complete
08:00 AM - Superset sends scheduled reports
All day  - Users query dashboards (cached results)
```

### Manual Triggering
```bash
# Full pipeline
docker compose exec dagster-web dagster asset materialize --select '*'

# Specific layer
docker compose exec dagster-web dagster asset materialize --select dbt_curated_models

# From specific asset onwards
docker compose exec dagster-web dagster asset materialize --select 'dbt_staging_models+'
```

## Data Formats at Each Stage

| Stage | Location | Format | Size (example) | Compression |
|-------|----------|--------|---------------|-------------|
| Raw | MinIO | Parquet | 500 MB | Snappy |
| Staging | DuckDB | View (pointer) | 0 MB | N/A |
| Curated | DuckDB | Table | 200 MB | None |
| Marts | Postgres | Table | 50 MB | None |

## Error Handling

### Failure Scenarios

**Scenario 1: Raw files missing**
- `raw_bioreactor_data` returns empty status
- Downstream assets skip (no data)
- Alert sent (future: add sensor alert)

**Scenario 2: dbt staging fails**
- dbt returns error
- Dagster marks asset failed
- Downstream assets blocked
- View logs in Dagster UI

**Scenario 3: Postgres mart fails**
- dbt postgres target fails
- DuckDB data remains valid
- Superset shows stale data
- Fix connection and re-run

### Retry Strategy
```python
# In Dagster (future enhancement)
@asset(retry_policy=RetryPolicy(max_retries=3, delay=60))
def dbt_staging_models(context, dbt):
    # Auto-retry on failure
    ...
```

## Performance Characteristics

### Bottlenecks
1. **Raw file size**: Large parquet files slow DuckDB scans
   - **Solution**: Partition by batch_id or date
2. **Staging views**: Complex views slow downstream queries
   - **Solution**: Materialize intermediate as tables
3. **Postgres write**: Bulk inserts can be slow
   - **Solution**: Use `COPY` instead of `INSERT`

### Optimization Tips
1. **DuckDB parallelism**: Set `threads=8` in profiles.yml
2. **Postgres indexes**: Add on filter/join columns
3. **Superset caching**: Enable chart cache (1 hour)
4. **Incremental dbt**: Use incremental models for large facts
5. **File size**: Keep parquet files 100MB-1GB each

## Monitoring the Flow

### Dagster UI (http://localhost:3000)
- Asset status: green (fresh) / yellow (stale) / red (failed)
- Lineage graph: visual dependencies
- Run history: execution logs

### Marquez UI (http://localhost:3002)
- End-to-end lineage
- Dataset versions
- Job run history

### Logs
```bash
# Full pipeline logs
docker compose logs dagster-webserver dagster-daemon

# dbt specific
docker compose exec dagster-web cat /opt/dagster/logs/dbt.log

# Postgres query logs
docker compose exec postgres tail -f /var/log/postgresql/postgresql.log
```

## Data Quality Checkpoints

### Current (Implicit)
- dbt tests (run with `dbt test`)
- Dagster asset checks (success/failure)

### Future (Explicit)
1. **Post-staging**: Great Expectations validation
   - Row count > threshold
   - No null batch_ids
   - Value ranges within limits

2. **Pre-marts**: Data freshness check
   - Latest batch_start within 24 hours
   - No duplicate batches

3. **Post-marts**: Business rule validation
   - All equipment_ids have data
   - avg_value matches expected range

## Extending the Flow

### Adding New Data Sources
1. Configure Airbyte connection
2. Land data in `/raw/{source_name}/`
3. Create dbt staging model `stg_{source}.sql`
4. Add to Dagster as asset
5. Join in curated layer

### Adding New Marts
1. Create dbt model in `marts_postgres/`
2. Tag with `mart`
3. Reference curated tables with `{{ ref() }}`
4. Run `dbt run --select tag:mart --target postgres`
5. Auto-appears in Dagster lineage

### Adding Sensors
```python
# Trigger on file arrival
@sensor(job=transform_job)
def raw_file_sensor(context):
    files = glob.glob('/data/lake/raw/bioreactor/*.parquet')
    new_files = [f for f in files if is_new(f)]
    if new_files:
        return RunRequest()
```

## Summary

The data flow is:
1. **Ingest** → MinIO (parquet)
2. **Stage** → DuckDB (views)
3. **Curate** → DuckDB (tables)
4. **Serve** → Postgres (marts)
5. **Visualize** → Superset (dashboards)
6. **Track** → Marquez (lineage)

All orchestrated by **Dagster** using an **asset-based** approach with explicit dependencies and automatic lineage tracking.
