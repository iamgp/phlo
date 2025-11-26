# Part 6: SQL Transformations with dbt—The Right Way

Raw data is in the lakehouse. Now we **transform** it into analysis-ready datasets using **dbt** (data build tool).

dbt solves a critical problem: **How do you manage SQL transformations professionally?**

## The Problem Without dbt

```python
# Without dbt: SQL in Python files (nightmare)

def transform_glucose():
    sql1 = """
    CREATE TABLE bronze_stg_entries AS
    SELECT _id, sgv, date_string FROM raw.entries
    WHERE sgv IS NOT NULL
    """
    trino.execute(sql1)
    
    sql2 = """
    CREATE TABLE silver_fct_readings AS
    SELECT
        entry_id,
        glucose_mg_dl,
        CASE WHEN glucose_mg_dl < 70 THEN 'hypoglycemia' END as category
    FROM bronze_stg_entries
    """
    trino.execute(sql2)
    
    sql3 = """
    CREATE TABLE gold_dim_date AS
    SELECT DISTINCT DATE(reading_timestamp) as reading_date
    FROM silver_fct_readings
    """
    trino.execute(sql3)
    
    # Problems:
    # 1. No documentation
    # 2. No testing (did the join work?)
    # 3. No lineage (which table depends on which?)
    # 4. No version control (what changed?)
    # 5. Manual dependency management (run sql3 after sql2)
```

## dbt Solves This

```sql
-- dbt: SQL with structure and discipline

-- File: models/bronze/stg_glucose_entries.sql
SELECT
    _id as entry_id,
    sgv as glucose_mg_dl,
    date_string as timestamp_iso,
    -- Comments documented
FROM {{ source('dagster_assets', 'glucose_entries') }}
WHERE sgv IS NOT NULL

-- File: models/silver/fct_glucose_readings.sql
SELECT
    entry_id,
    glucose_mg_dl,
    CASE
        WHEN glucose_mg_dl < 70 THEN 'hypoglycemia'
        WHEN glucose_mg_dl <= 180 THEN 'in_range'
        ELSE 'hyperglycemia'
    END as glucose_category
FROM {{ ref('stg_glucose_entries') }}  -- Auto-dependency!

-- File: models/gold/dim_date.sql
SELECT DISTINCT DATE(reading_timestamp) as reading_date
FROM {{ ref('fct_glucose_readings') }}  -- dbt finds dependencies
```

One command runs everything:
```bash
dbt build
# dbt figures out: run bronze first, then silver, then gold
# Tests each transformation
# Generates documentation
```

## dbt's Four Core Features

### 1. Models (Reusable SQL)

A model is a `.sql` file that transforms data:

```sql
-- models/bronze/stg_glucose_entries.sql
{{ config(
    materialized='view',  -- or 'table' for persistent storage
    tags=['nightscout'],   -- organize models
) }}

-- CTEs for clarity
WITH raw_data AS (
    SELECT * FROM {{ source('dagster_assets', 'glucose_entries') }}
),

cleaned AS (
    SELECT
        _id as entry_id,
        sgv as glucose_mg_dl,
        date_string as timestamp_iso,
        -- More transformations
    FROM raw_data
    WHERE sgv IS NOT NULL
)

SELECT * FROM cleaned
```

dbt materializes this as:
- **View**: Query source every time (slow for complex transforms)
- **Table**: Precompute once, fast queries (Phlo uses this)
- **Incremental**: Only process new data (for huge tables)

Phlo's config:

```sql
-- Bronze models
{{ config(materialized='view') }}
-- Staging layer, not persisted

-- Silver models
{{ config(materialized='table') }}
-- Fact tables, persisted in Iceberg

-- Gold models
{{ config(materialized='table') }}
-- Dimensions, persisted in Iceberg
```

### 2. Dependencies (Auto-Resolved)

Instead of manual ordering, dbt resolves dependencies:

```sql
-- Model A: source data
FROM {{ source('dagster_assets', 'glucose_entries') }}

-- Model B: depends on Model A
FROM {{ ref('stg_glucose_entries') }}  -- ref('A')

-- Model C: depends on Model B
FROM {{ ref('fct_glucose_readings') }}  -- ref('B')
```

dbt builds a DAG (directed acyclic graph):

```
glucose_entries (source)
    ↓ (Model A)
stg_glucose_entries
    ↓ (Model B)
fct_glucose_readings
    ↓ (Model C)
dim_date, mrt_glucose_readings
    ↓ (Model D)
gold/marts tables
```

Execute order: automatic!

### 3. Testing (Data Quality)

dbt includes built-in tests:

```yaml
# models/silver/fct_glucose_readings.yml
version: 2

models:
  - name: fct_glucose_readings
    description: Enriched glucose readings with business logic
    columns:
      - name: entry_id
        tests:
          - unique      # Each entry_id appears once
          - not_null    # No missing values
          
      - name: glucose_mg_dl
        tests:
          - not_null
          - accepted_values:
              values: [0]  # 0 for missing data
              
      - name: glucose_category
        tests:
          - accepted_values:
              values: ['hypoglycemia', 'in_range', 'hyperglycemia_mild', 'hyperglycemia_severe']
```

Run tests:
```bash
dbt test

# Output
Running with dbt=1.8.0
Found 3 models, 8 tests...

Testing fct_glucose_readings
  Running test unique_fct_glucose_readings_entry_id ... PASS
  Running test not_null_fct_glucose_readings_entry_id ... PASS
  Running test accepted_values_fct_glucose_readings_glucose_category ... PASS
```

### 4. Documentation (Auto-Generated)

dbt generates a knowledge base from YAML:

```yaml
# models/silver/schema.yml
version: 2

models:
  - name: fct_glucose_readings
    description: |
      Enriched glucose readings with calculated metrics.
      Serves as foundation for all downstream analytics.
    
    columns:
      - name: entry_id
        description: Unique Nightscout entry ID (MongoDB ObjectId)
        
      - name: glucose_mg_dl
        description: Glucose reading in mg/dL
        tests:
          - not_null
          
      - name: glucose_category
        description: Classification (hypoglycemia/in_range/hyperglycemia)
        
      - name: hour_of_day
        description: Hour extracted from reading_timestamp (0-23)
```

Run:
```bash
dbt docs generate
dbt docs serve  # Opens http://localhost:8000

# Generates interactive documentation with:
# - Column descriptions
# - Test results
# - Data lineage (visual DAG)
# - Query execution stats
```

## Phlo's dbt Structure

### Directory Layout

```
transforms/dbt/
├── models/
│   ├── sources.yml         # External data sources (raw Iceberg tables)
│   ├── bronze/
│   │   ├── stg_glucose_entries.sql    # Staging (filter, rename, validate)
│   │   ├── stg_github_user_events.sql
│   │   └── stg_*.sql
│   ├── silver/
│   │   ├── fct_glucose_readings.sql   # Fact tables (business logic)
│   │   ├── fct_github_user_events.sql
│   │   └── fct_*.sql
│   ├── gold/
│   │   ├── dim_date.sql               # Dimensions
│   │   ├── mrt_glucose_readings.sql   # Metrics
│   │   └── *.sql
│   └── marts_postgres/
│       ├── mrt_glucose_overview.sql   # Publish to Postgres
│       └── *.sql
├── tests/
│   └── custom_tests.sql               # Custom SQL tests
├── profiles.yml                       # Connection config
└── dbt_project.yml                   # Project config
```

### 4-Layer Architecture

1. **Bronze** (Staging):
   - Raw data cleanup
   - Type conversions
   - Rename columns
   - Filter obvious errors

   ```sql
   -- stg_glucose_entries.sql
   SELECT
       _id as entry_id,
       CAST(sgv as INT) as glucose_mg_dl,
       CAST(date_string as TIMESTAMP) as timestamp_iso
   FROM {{ source('dagster_assets', 'glucose_entries') }}
   WHERE sgv IS NOT NULL
   ```

2. **Silver** (Fact Tables):
   - Business logic
   - Calculations
   - Joins and enrichment
   - Metrics

   ```sql
   -- fct_glucose_readings.sql
   SELECT
       entry_id,
       glucose_mg_dl,
       CASE
           WHEN glucose_mg_dl < 70 THEN 'hypoglycemia'
           WHEN glucose_mg_dl <= 180 THEN 'in_range'
           ELSE 'hyperglycemia'
       END as glucose_category,
       -- Rate of change (lag window function)
       glucose_mg_dl - LAG(glucose_mg_dl) OVER (
           PARTITION BY device ORDER BY reading_timestamp
       ) as glucose_change_mg_dl
   FROM {{ ref('stg_glucose_entries') }}
   ```

3. **Gold** (Dimensions):
   - Pre-computed dimensions
   - Slow-changing dimensions
   - Reference tables

   ```sql
   -- dim_date.sql
   SELECT DISTINCT
       DATE(reading_timestamp) as reading_date,
       EXTRACT(YEAR FROM reading_timestamp) as year,
       EXTRACT(QUARTER FROM reading_timestamp) as quarter,
       EXTRACT(MONTH FROM reading_timestamp) as month,
       EXTRACT(WEEK FROM reading_timestamp) as week,
       EXTRACT(DAY_OF_WEEK FROM reading_timestamp) as day_of_week
   FROM {{ ref('fct_glucose_readings') }}
   ORDER BY reading_date
   ```

4. **Marts** (Published):
   - Business-ready tables
   - Published to Postgres for BI tools
   - Aggregations and summaries

   ```sql
   -- marts_postgres/mrt_glucose_overview.sql
   SELECT
       reading_date,
       ROUND(AVG(glucose_mg_dl), 1) as avg_glucose,
       MIN(glucose_mg_dl) as min_glucose,
       MAX(glucose_mg_dl) as max_glucose,
       COUNT(*) as reading_count,
       ROUND(100.0 * SUM(CASE WHEN is_in_range THEN 1 ELSE 0 END)
             / COUNT(*), 1) as percent_in_range
   FROM {{ ref('fct_glucose_readings') }}
   GROUP BY reading_date
   ORDER BY reading_date DESC
   ```

## Integration with Phlo

### Connection Configuration

Nessie branching is configured via different Trino catalogs:

```yaml
# profiles.yml
phlo:
  target: dev  # development by default
  
  outputs:
    dev:
      type: trino
      host: trino
      port: 8080
      catalog: iceberg_dev  # Dev branch catalog
      schema: bronze
    
    prod:
      type: trino
      host: trino
      port: 8080
      catalog: iceberg      # Main branch catalog
      schema: bronze
```

The `iceberg_dev` catalog points to the Nessie dev branch, while `iceberg` points to main.
This is configured in Trino's catalog properties, not via session properties.

### Partition-Aware Execution

dbt runs on daily partitions (via Dagster):

```sql
-- models/silver/fct_glucose_readings.sql
{{ config(
    materialized='table',
) }}

SELECT
    entry_id,
    glucose_mg_dl,
    ...
FROM {{ ref('stg_glucose_entries') }}
{% if var('partition_date_str', None) is not none %}
-- Filter to partition when running daily
WHERE DATE(reading_timestamp) = DATE('{{ var("partition_date_str") }}')
{% endif %}
```

Dagster passes partition date:

```python
# From defs/transform/dbt.py

if context.has_partition_key:
    partition_date = context.partition_key
    build_args.extend([
        "--vars",
        f'{{"partition_date_str": "{partition_date}"}}'
    ])
```

## Hands-On: Run dbt Transforms

### Option 1: Via Dagster UI

1. Open http://localhost:3000
2. Click asset: `stg_glucose_entries`
3. Click **Materialize**
4. Watch dbt run in logs

### Option 2: Direct Command

```bash
# Run all models
docker exec dagster-webserver dbt build \
  --project-dir /transforms/dbt \
  --profiles-dir /transforms/dbt/profiles \
  --target dev

# Run specific model
docker exec dagster-webserver dbt run \
  --project-dir /transforms/dbt \
  --profiles-dir /transforms/dbt/profiles \
  --select stg_glucose_entries

# Run with tests
docker exec dagster-webserver dbt test \
  --project-dir /transforms/dbt \
  --profiles-dir /transforms/dbt/profiles
```

### Option 3: Local (if you have uv installed)

```bash
cd transforms/dbt

# Install dbt
uv pip install dbt-trino

# Create dbt profiles
mkdir -p ~/.dbt
cat > ~/.dbt/profiles.yml << EOF
phlo:
  target: dev
  outputs:
    dev:
      type: trino
      host: localhost
      port: 8080
      catalog: iceberg
      schema: bronze
EOF

# Run dbt
dbt run --select stg_glucose_entries
dbt test
dbt docs generate && dbt docs serve
```

## Best Practices in dbt

### 1. Naming Convention

```
bronze/stg_*              Staging (from source)
silver/fct_*              Fact tables
silver/dim_*              Dimension tables
gold/*                    Summarized/published
marts_postgres/*          Published to Postgres
```

### 2. CTEs for Clarity

```sql
-- Good: logical steps with CTEs
WITH source_data AS (
    SELECT * FROM {{ source(...) }}
),
cleaned AS (
    SELECT ... FROM source_data WHERE ...
),
enriched AS (
    SELECT ... FROM cleaned
)
SELECT * FROM enriched

-- Bad: nested subqueries (hard to read)
SELECT * FROM (
    SELECT ... FROM (
        SELECT * FROM ...
    ) sub
) outer_sub
```

### 3. Comments for Complex Logic

```sql
-- Document the "why" not the "what"
SELECT
    entry_id,
    -- Rate of change: glucose difference from previous reading
    -- Used to identify rapid spikes (potential errors)
    glucose_mg_dl - LAG(glucose_mg_dl) OVER (...) as glucose_change
FROM {{ ref('stg_glucose_entries') }}
```

### 4. Tests for Critical Columns

```yaml
columns:
  - name: entry_id
    tests:
      - unique       # Must be unique
      - not_null     # Cannot be missing
  
  - name: glucose_mg_dl
    tests:
      - not_null
      - dbt_utils.accepted_range:
          min_value: 20
          max_value: 600
```

## Performance Tips

### 1. Incremental Models (Large Tables)

For tables with millions of rows, use incremental:

```sql
{{ config(
    materialized='incremental',
    unique_key='entry_id',
    on_schema_change='fail',
) }}

SELECT *
FROM {{ source('raw', 'entries') }}

{% if execute %}
  {% set max_partition = run_started_at %}
  WHERE _cascade_ingested_at > '{{ max_partition }}'
{% endif %}
```

Only processes new data since last run.

### 2. Limit in Development

```sql
SELECT * FROM {{ ref('large_table') }}
{% if execute and execute_sql %}
  LIMIT 1000  -- Don't scan 100M rows while developing
{% endif %}
```

### 3. Pre-filter Before Joins

```sql
-- Bad: Join large tables then filter
SELECT * FROM {{ ref('fact') }}
LEFT JOIN {{ ref('dimension') }} ...
WHERE dimension.active = true

-- Good: Filter dimension first
SELECT * FROM {{ ref('fact') }}
LEFT JOIN (
    SELECT * FROM {{ ref('dimension') }}
    WHERE active = true
) dim ...
```

## Next: Orchestration

We have ingestion and transformation. Now: **Who runs this, and when?**

**Part 7: Orchestration with Dagster**

See you there!

## Summary

**dbt provides**:
- Reusable SQL models
- Auto-resolved dependencies
- Built-in data quality tests
- Documentation generation
- Version control (git-friendly)

**Phlo uses dbt for**:
- Bronze: Raw data staging
- Silver: Fact tables with business logic
- Gold: Dimensions and metrics
- Marts: Published to Postgres for BI

**Key Pattern**: Define models as SQL files, dbt handles orchestration and testing.

**Next**: [Part 7: Orchestration with Dagster—Running Your Pipelines](07-orchestration-dagster.md)
