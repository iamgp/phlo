# dbt (Data Build Tool)

## Overview

dbt transforms raw data into analytics-ready datasets using SQL. It manages the entire transformation layer of the lakehouse, from staging to final marts.

## Project Structure

```
dbt/
├── dbt_project.yml          # Project configuration
├── profiles/
│   └── profiles.yml         # Connection profiles
├── models/
│   ├── staging/            # Raw → cleaned data
│   │   └── stg_bioreactor.sql
│   ├── intermediate/       # Business logic
│   │   └── int_bioreactor_downsample_5m.sql
│   ├── curated/           # Analytical models
│   │   ├── dim_batch.sql
│   │   └── fact_bioreactor_batch_stats.sql
│   └── marts_postgres/    # BI-ready tables
│       └── mart_bioreactor_overview.sql
├── macros/                # Custom SQL functions
├── seeds/                 # CSV reference data
└── target/               # Compiled SQL & manifest.json
```

## Configuration

### dbt_project.yml
```yaml
name: cg_lakehouse
version: 1.0.0
profile: cg_lakehouse

models:
  cg_lakehouse:
    staging:
      +schema: staging
      +materialized: view
      +tags: ["stg"]
    intermediate:
      +schema: intermediate
      +tags: ["int"]
    curated:
      +schema: curated
      +tags: ["curated"]
      +materialized: table
    marts_postgres:
      +schema: marts
      +tags: ["mart"]
      +materialized: table
```

### profiles.yml
Two targets for dual-database architecture:

```yaml
cg_lakehouse:
  target: duckdb
  outputs:
    duckdb:  # For transformation
      type: duckdb
      path: /data/duckdb/warehouse.duckdb
      extensions: ["httpfs", "json", "parquet"]
      config:
        s3_endpoint: minio:9000
        s3_access_key_id: "{{ env_var('MINIO_ROOT_USER') }}"
        s3_secret_access_key: "{{ env_var('MINIO_ROOT_PASSWORD') }}"

    postgres:  # For marts
      type: postgres
      host: postgres
      user: "{{ env_var('POSTGRES_USER') }}"
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: marts
```

## Model Layers

### 1. Staging (stg_*)
**Purpose**: Clean, standardize, and type raw data
**Materialization**: Views (no storage)
**Target**: DuckDB

```sql
-- models/staging/stg_bioreactor.sql
{{ config(materialized='view') }}

SELECT
  cast(batch_id as varchar) as batch_id,
  equipment_id,
  ts::timestamp as ts,
  cast(tag as varchar) as tag,
  cast(value as double) as value,
  site
FROM read_parquet('/data/lake/raw/bioreactor/*.parquet');
```

**Best Practices**:
- 1:1 mapping with source files
- Renaming columns to snake_case
- Type casting and parsing
- No business logic
- Light cleaning only

### 2. Intermediate (int_*)
**Purpose**: Reusable business logic
**Materialization**: Views or ephemeral
**Target**: DuckDB

```sql
-- models/intermediate/int_bioreactor_downsample_5m.sql
{{ config(materialized='view', tags=['int']) }}

SELECT
  batch_id,
  equipment_id,
  time_bucket(interval '5 minutes', ts) as ts_5m,
  tag,
  avg(value) as avg_value,
  min(value) as min_value,
  max(value) as max_value
FROM {{ ref('stg_bioreactor') }}
GROUP BY batch_id, equipment_id, ts_5m, tag
```

**Best Practices**:
- Reference staging with `{{ ref('stg_model') }}`
- Single-purpose transformations
- Reusable across multiple downstream models

### 3. Curated (dim_*, fact_*)
**Purpose**: Dimensional and fact tables
**Materialization**: Tables (persisted)
**Target**: DuckDB

```sql
-- models/curated/dim_batch.sql
{{ config(materialized='table', tags=['curated']) }}

SELECT DISTINCT
  batch_id,
  equipment_id,
  site,
  min(ts) as batch_start,
  max(ts) as batch_end
FROM {{ ref('stg_bioreactor') }}
GROUP BY batch_id, equipment_id, site
```

```sql
-- models/curated/fact_bioreactor_batch_stats.sql
{{ config(materialized='table', tags=['curated']) }}

SELECT
  b.batch_id,
  b.equipment_id,
  b.batch_start,
  b.batch_end,
  br.tag,
  avg(br.value) as avg_value,
  min(br.value) as min_value,
  max(br.value) as max_value,
  count(*) as record_count
FROM {{ ref('dim_batch') }} b
JOIN {{ ref('stg_bioreactor') }} br
  ON b.batch_id = br.batch_id
GROUP BY b.batch_id, b.equipment_id, b.batch_start, b.batch_end, br.tag
```

### 4. Marts (mart_*)
**Purpose**: Analytics-ready, denormalized tables for BI
**Materialization**: Tables (persisted)
**Target**: **Postgres** (different database!)

```sql
-- models/marts_postgres/mart_bioreactor_overview.sql
{{ config(
    materialized='table',
    tags=['mart']
) }}

SELECT
  b.batch_id,
  b.equipment_id,
  b.site,
  b.batch_start,
  b.batch_end,
  s.tag,
  s.avg_value,
  s.min_value,
  s.max_value,
  s.record_count
FROM {{ ref('dim_batch') }} b
LEFT JOIN {{ ref('fact_bioreactor_batch_stats') }} s
  ON b.batch_id = s.batch_id
  AND b.equipment_id = s.equipment_id
```

## Running dbt

### From Dagster
Dagster orchestrates dbt via assets:
- **UI**: Materialize dbt assets at http://localhost:3000
- **Automatic**: `nightly_pipeline` schedule runs at 2 AM

### Manual Execution
```bash
# Access dbt in container
docker compose exec dagster-web bash

# Run all models (DuckDB target)
dbt run

# Run specific models
dbt run --select stg_bioreactor
dbt run --select tag:curated
dbt run --models staging/

# Run with different target
dbt run --select tag:mart --target postgres

# Test models
dbt test

# Generate docs
dbt docs generate
dbt docs serve  # Won't work in container
```

### Selection Syntax
```bash
# By tag
dbt run --select tag:stg
dbt run --select tag:int tag:curated

# By path
dbt run --select staging/
dbt run --select models/curated/

# By name pattern
dbt run --select stg_*
dbt run --select +mart_bioreactor_overview  # Include upstream

# Downstream only
dbt run --select stg_bioreactor+
```

## Testing

### Schema Tests
Define in `schema.yml`:
```yaml
# models/staging/schema.yml
version: 2

models:
  - name: stg_bioreactor
    description: "Staged bioreactor data from raw parquet"
    columns:
      - name: batch_id
        description: "Unique batch identifier"
        tests:
          - not_null
          - unique
      - name: value
        tests:
          - not_null
      - name: tag
        tests:
          - accepted_values:
              values: ['temperature', 'ph', 'do', 'pressure']
```

### Custom Tests
```sql
-- tests/assert_positive_values.sql
SELECT *
FROM {{ ref('stg_bioreactor') }}
WHERE value < 0
```

### Run Tests
```bash
# All tests
dbt test

# Specific model
dbt test --select stg_bioreactor

# By type
dbt test --select test_type:schema
dbt test --select test_type:custom
```

## Incremental Models

For large datasets, use incremental materialization:

```sql
{{ config(
    materialized='incremental',
    unique_key='batch_id'
) }}

SELECT
  batch_id,
  equipment_id,
  ts,
  tag,
  value
FROM {{ ref('stg_bioreactor') }}

{% if is_incremental() %}
  -- Only new/updated records
  WHERE ts > (SELECT max(ts) FROM {{ this }})
{% endif %}
```

## Snapshots (Type 2 SCD)

Track historical changes:

```sql
-- snapshots/dim_batch_snapshot.sql
{% snapshot dim_batch_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='batch_id',
      strategy='timestamp',
      updated_at='batch_end',
    )
}}

SELECT * FROM {{ ref('dim_batch') }}

{% endsnapshot %}
```

Run snapshots:
```bash
dbt snapshot
```

## Macros

Reusable SQL functions:

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name, scale=2) %}
  round({{ column_name }} / 100, {{ scale }})
{% endmacro %}
```

Usage in models:
```sql
SELECT
  batch_id,
  {{ cents_to_dollars('cost_cents') }} as cost_dollars
FROM {{ ref('dim_batch') }}
```

## Documentation

### Model Documentation
```yaml
# models/schema.yml
version: 2

models:
  - name: dim_batch
    description: |
      Batch dimension table containing metadata about each manufacturing batch.
      Updated daily via dbt.
    columns:
      - name: batch_id
        description: "Primary key, unique batch identifier"
      - name: batch_start
        description: "Timestamp when batch processing started"
```

### Generate Docs
```bash
dbt docs generate
```

This creates `target/manifest.json` used by Dagster for asset lineage.

## Debugging

### Compiled SQL
View compiled queries:
```bash
# Compile without running
dbt compile --select stg_bioreactor

# View compiled SQL
cat target/compiled/cg_lakehouse/staging/stg_bioreactor.sql
```

### Run Logs
```bash
# Verbose logging
dbt run --select stg_bioreactor --debug

# Log to file
dbt run > dbt_run.log 2>&1
```

### Dry Run
```bash
# Show what would run
dbt run --select stg_bioreactor --dry-run
```

## Environment Variables

Set in `docker-compose.yml`:
```yaml
DBT_PROFILES_DIR: /dbt/profiles
POSTGRES_USER: lake
POSTGRES_PASSWORD: lakepass
POSTGRES_DB: lakehouse
MINIO_ROOT_USER: minio
MINIO_ROOT_PASSWORD: minio999
```

Reference in `profiles.yml`:
```yaml
user: "{{ env_var('POSTGRES_USER') }}"
```

## Performance Optimization

### 1. Materialization Strategy
- **Views**: Fast to build, slow to query (staging)
- **Tables**: Slow to build, fast to query (curated, marts)
- **Ephemeral**: No persistence, inlined SQL (intermediate)
- **Incremental**: Only process new data

### 2. Parallelization
```bash
# Use multiple threads
dbt run --threads 8
```

Set in `profiles.yml`:
```yaml
duckdb:
  type: duckdb
  threads: 8
```

### 3. Limit Data in Dev
```sql
{{ config(materialized='view') }}

SELECT * FROM {{ ref('stg_bioreactor') }}

{% if target.name == 'dev' %}
  LIMIT 10000
{% endif %}
```

## Multi-Target Workflow

### Default: DuckDB (Transformation)
```bash
dbt run  # Uses duckdb target
```

### Switch to Postgres (Marts)
```bash
dbt run --select tag:mart --target postgres
```

### In Dagster
```python
# DuckDB models
dbt.cli(["run", "--select", "tag:curated"], target="duckdb")

# Postgres models
dbt.cli(["run", "--select", "tag:mart"], target="postgres")
```

## Troubleshooting

### Model Not Found
```bash
# Verify model exists
ls dbt/models/staging/stg_bioreactor.sql

# Check dbt can see it
dbt ls --select stg_bioreactor
```

### Target Database Issues
```bash
# Test connection
dbt debug

# Specific target
dbt debug --target postgres
```

### Compilation Errors
```bash
# Check for syntax errors
dbt compile --select problematic_model

# View error details
cat target/run_results.json
```

### Permission Errors
```sql
-- In postgres, grant permissions
GRANT ALL ON SCHEMA marts TO lake;
GRANT ALL ON ALL TABLES IN SCHEMA marts TO lake;
```

## Best Practices

1. **Naming**: `stg_`, `int_`, `dim_`, `fact_`, `mart_` prefixes
2. **One Model = One File**: Each model in separate `.sql` file
3. **DRY**: Use macros for repeated logic
4. **Documentation**: Document all models and columns
5. **Tests**: Add tests for all critical models
6. **Incremental**: Use for large fact tables
7. **Staging**: Always stage raw data first
8. **Target Separation**: DuckDB for transformation, Postgres for serving

## Next Steps

- [dbt + Dagster Integration](../integrations/dagster-dbt.md)
- [dbt + DuckDB Patterns](../integrations/dbt-duckdb.md)
- [Testing Strategy Guide](../guides/testing-strategy.md)
