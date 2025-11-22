# dbt Development Guide

## SQL Transformations Made Easy

This guide teaches you how to use dbt effectively in Phlo for data transformations.

---

## Table of Contents

1. [dbt Basics](#dbt-basics)
2. [Project Structure](#project-structure)
3. [Sources](#sources)
4. [Models](#models)
5. [Tests](#tests)
6. [Documentation](#documentation)
7. [Macros and Functions](#macros-and-functions)
8. [Incremental Models](#incremental-models)
9. [Best Practices](#best-practices)

---

## dbt Basics

### What is dbt?

**dbt** (data build tool) transforms data in your warehouse using SQL SELECT statements.

**Philosophy:**
- Transformations are SELECT statements (not INSERT/UPDATE)
- Version control your SQL
- Test data quality automatically
- Generate documentation automatically
- Manage dependencies automatically

### How dbt Works

```
1. You write: models/my_model.sql
   SELECT * FROM source_table WHERE active = true

2. dbt generates: CREATE TABLE my_schema.my_model AS
   SELECT * FROM source_table WHERE active = true

3. dbt runs it in your warehouse (Trino)

4. Result: Table created!
```

### dbt in Phlo

**Location:** `transforms/dbt/`

**Configuration:** `transforms/dbt/dbt_project.yml`

**Profile:** `transforms/dbt/profiles/profiles.yml` (Trino connection)

**Models:** `transforms/dbt/models/`

**Integration:** Dag ster runs dbt and tracks lineage automatically

---

## Project Structure

```
transforms/dbt/
├── dbt_project.yml          # Project configuration
├── profiles/
│   └── profiles.yml          # Connection settings
│
├── models/
│   ├── sources/              # Source definitions
│   │   ├── sources.yml
│   │   └── sources_weather.yml
│   │
│   ├── bronze/               # Staging models
│   │   ├── stg_glucose_entries.sql
│   │   ├── stg_weather_observations.sql
│   │   └── schema.yml        # Tests and documentation
│   │
│   ├── silver/               # Fact/dimension models
│   │   ├── fct_glucose_readings.sql
│   │   ├── fct_weather_readings.sql
│   │   └── schema.yml
│   │
│   ├── gold/                 # Aggregations
│   │   ├── agg_daily_weather_summary.sql
│   │   └── schema.yml
│   │
│   └── marts_postgres/       # Published marts
│       ├── mrt_glucose_overview.sql
│       └── schema.yml
│
├── macros/                   # Reusable SQL functions
│   └── generate_schema_name.sql
│
├── tests/                    # Custom data tests
│   └── assert_positive_values.sql
│
└── target/                   # Generated files (gitignored)
    ├── manifest.json         # Dependency graph
    ├── run_results.json      # Test results
    └── compiled/             # Compiled SQL
```

---

## Sources

### What are Sources?

**Sources** are raw tables (not created by dbt) that you want to transform.

### Defining Sources

Create: `models/sources/sources_weather.yml`

```yaml
version: 2

sources:
  - name: raw
    description: "Raw data layer"
    schema: raw  # Iceberg schema
    database: iceberg  # Trino catalog

    tables:
      - name: weather_observations
        description: "Raw weather data from OpenWeather API"
        columns:
          - name: city_name
            description: "City name"
            tests:
              - not_null

          - name: temperature
            description: "Temperature in Celsius"
            tests:
              - not_null

          - name: observation_time
            description: "When observation was recorded"
            tests:
              - not_null
              - dbt_utils.at_least_one

      - name: glucose_entries
        description: "Raw glucose readings from Nightscout"
        # ... columns
```

### Referencing Sources

In your models:

```sql
-- Use source() function
SELECT *
FROM {{ source('raw', 'weather_observations') }}

-- dbt generates:
-- SELECT * FROM iceberg.raw.weather_observations
```

**Benefits:**
- dbt knows dependencies
- Tests run on source data
- Documentation auto-generated
- Source freshness checks

### Source Freshness

Check if source data is stale:

```yaml
sources:
  - name: raw
    freshness:
      warn_after: {count: 2, period: hour}
      error_after: {count: 24, period: hour}

    tables:
      - name: weather_observations
        loaded_at_field: observation_time
        freshness:
          warn_after: {count: 1, period: hour}
```

Check freshness:
```bash
dbt source freshness --project-dir /opt/dagster/app/transforms/dbt
```

---

## Models

### What are Models?

**Models** are SELECT statements that create tables/views.

### Basic Model

Create: `models/bronze/stg_weather_observations.sql`

```sql
SELECT
    city_name,
    CAST(temperature AS DOUBLE) AS temperature_c,
    CAST(observation_time AS TIMESTAMP) AS observation_timestamp
FROM {{ source('raw', 'weather_observations') }}
WHERE temperature IS NOT NULL
```

### Model Configuration

**In-file config:**

```sql
{{
    config(
        materialized='table',      # table, view, incremental, ephemeral
        schema='bronze',            # Target schema
        tags=['weather', 'bronze'], # Tags for selection
        alias='weather_staging',    # Override table name
    )
}}

SELECT * FROM {{ source('raw', 'weather_observations') }}
```

**In dbt_project.yml:**

```yaml
models:
  phlo:
    # All models default to table
    materialized: table

    bronze:
      # Bronze models are views (fast, always fresh)
      materialized: view
      schema: bronze

    silver:
      # Silver models are tables (fast queries)
      materialized: table
      schema: silver

    gold:
      materialized: table
      schema: gold
```

### Materialization Types

**1. Table (default)**
```sql
{{ config(materialized='table') }}

-- Creates: CREATE TABLE silver.my_model AS SELECT ...
-- Pros: Fast queries
-- Cons: Takes time to rebuild
```

**2. View**
```sql
{{ config(materialized='view') }}

-- Creates: CREATE VIEW bronze.my_model AS SELECT ...
-- Pros: Always fresh, fast to "build"
-- Cons: Slow queries (re-runs SELECT every time)
```

**3. Incremental**
```sql
{{ config(materialized='incremental', unique_key='id') }}

SELECT * FROM {{ source('raw', 'events') }}

{% if is_incremental() %}
    -- Only new records since last run
    WHERE created_at > (SELECT MAX(created_at) FROM {{ this }})
{% endif %}

-- Pros: Fast builds (only new data)
-- Cons: More complex logic
```

**4. Ephemeral**
```sql
{{ config(materialized='ephemeral') }}

-- Not materialized - just a CTE in downstream models
-- Pros: No table created
-- Cons: Can't query directly
```

### Referencing Models

```sql
-- Use ref() function
SELECT *
FROM {{ ref('stg_weather_observations') }}

-- dbt generates:
-- SELECT * FROM iceberg.bronze.stg_weather_observations

-- And tracks the dependency!
```

**Dependency graph automatically built:**
```
raw.weather_observations (source)
    ↓
stg_weather_observations (ref)
    ↓
fct_weather_readings (ref)
```

### Model Selection

**Run specific model:**
```bash
dbt run --select stg_weather_observations
```

**Run model and upstream:**
```bash
dbt run --select +stg_weather_observations
```

**Run model and downstream:**
```bash
dbt run --select stg_weather_observations+
```

**Run by tag:**
```bash
dbt run --select tag:weather
```

**Run by directory:**
```bash
dbt run --select bronze.*
```

**Exclude models:**
```bash
dbt run --exclude tag:deprecated
```

---

## Tests

### Built-in Tests

Add to `schema.yml`:

```yaml
version: 2

models:
  - name: fct_weather_readings
    description: "Weather readings with metrics"
    columns:
      - name: city_name
        description: "City name"
        tests:
          - not_null           # No NULL values
          - unique             # No duplicates

      - name: temperature_c
        description: "Temperature in Celsius"
        tests:
          - not_null
          - accepted_values:
              values: [-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50]
              quote: false
          - dbt_utils.accepted_range:
              min_value: -50
              max_value: 60

      - name: temp_category
        tests:
          - accepted_values:
              values: ['Freezing', 'Cold', 'Mild', 'Warm', 'Hot']

      - name: observation_timestamp
        tests:
          - not_null
          - dbt_utils.recency:
              datepart: hour
              field: observation_timestamp
              interval: 24
```

### Custom SQL Tests

Create: `tests/assert_reasonable_temperatures.sql`

```sql
-- Test passes if query returns zero rows
-- Test fails if query returns any rows

SELECT
    city_name,
    temperature_c,
    observation_timestamp
FROM {{ ref('fct_weather_readings') }}
WHERE
    temperature_c < -60  -- Unreasonably cold
    OR temperature_c > 60  -- Unreasonably hot
```

### Relationship Tests

Ensure foreign keys are valid:

```yaml
models:
  - name: fct_orders
    columns:
      - name: customer_id
        tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id
```

### Running Tests

```bash
# Run all tests
dbt test --project-dir /opt/dagster/app/transforms/dbt

# Test specific model
dbt test --select fct_weather_readings

# Test specific column
dbt test --select fct_weather_readings,column:temperature_c

# Run only data tests (not schema tests)
dbt test --data

# Run only schema tests
dbt test --schema
```

### Test Severity

```yaml
columns:
  - name: temperature_c
    tests:
      - not_null:
          severity: error  # Fails build (default)

      - accepted_values:
          values: [...]
          severity: warn   # Warning only, doesn't fail
```

---

## Documentation

### Column Documentation

```yaml
models:
  - name: fct_weather_readings
    description: |
      Weather readings with calculated metrics and categorizations.

      This model:
      - Converts temperature to Fahrenheit
      - Categorizes temperature (Freezing/Cold/Mild/Warm/Hot)
      - Calculates comfort level
      - Determines daytime vs nighttime

    columns:
      - name: city_name
        description: "Name of the city"

      - name: temperature_c
        description: |
          Temperature in Celsius as reported by the weather service.
          Negative values indicate below freezing.

      - name: temp_category
        description: |
          Temperature category based on Celsius value:
          - Freezing: < 0°C
          - Cold: 0-10°C
          - Mild: 10-20°C
          - Warm: 20-30°C
          - Hot: > 30°C
```

### Generating Documentation

```bash
# Generate docs
dbt docs generate --project-dir /opt/dagster/app/transforms/dbt

# Serve docs locally
dbt docs serve --project-dir /opt/dagster/app/transforms/dbt --port 8080

# Open browser to http://localhost:8080
```

### Documentation Features

- **Lineage graph** - Visual dependency diagram
- **Column details** - Descriptions, types, tests
- **Model code** - SQL source code
- **Test results** - Pass/fail status
- **Source freshness** - Last updated times

---

## Macros and Functions

### What are Macros?

**Macros** are reusable SQL snippets (like functions).

### Creating Macros

Create: `macros/temperature_category.sql`

```sql
{% macro temperature_category(temp_column) %}
    CASE
        WHEN {{ temp_column }} < 0 THEN 'Freezing'
        WHEN {{ temp_column }} < 10 THEN 'Cold'
        WHEN {{ temp_column }} < 20 THEN 'Mild'
        WHEN {{ temp_column }} < 30 THEN 'Warm'
        ELSE 'Hot'
    END
{% endmacro %}
```

### Using Macros

```sql
SELECT
    city_name,
    temperature_c,
    {{ temperature_category('temperature_c') }} AS temp_category
FROM {{ ref('stg_weather_observations') }}

-- Compiles to:
-- CASE
--     WHEN temperature_c < 0 THEN 'Freezing'
--     ...
-- END AS temp_category
```

### Built-in dbt Macros

```sql
-- Current timestamp
{{ dbt_utils.current_timestamp() }}

-- Generate surrogate key
{{ dbt_utils.generate_surrogate_key(['city_name', 'observation_time']) }}

-- Date spine (generate date series)
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2024-01-01' as date)",
    end_date="cast('2024-12-31' as date)"
) }}

-- Union tables
{{ dbt_utils.union_relations(
    relations=[ref('table1'), ref('table2')]
) }}
```

### Jinja Control Flow

```sql
{% set cities = ['London', 'New York', 'Tokyo'] %}

SELECT *
FROM {{ ref('weather_observations') }}
WHERE city_name IN (
    {% for city in cities %}
        '{{ city }}'{% if not loop.last %},{% endif %}
    {% endfor %}
)

-- Compiles to:
-- WHERE city_name IN ('London', 'New York', 'Tokyo')
```

### Conditional Logic

```sql
{% if target.name == 'prod' %}
    -- Production-only logic
    WHERE is_verified = true
{% else %}
    -- Development: all data
    WHERE 1=1
{% endif %}
```

---

## Incremental Models

### What are Incremental Models?

Process only **new** data since last run (not full refresh).

### Basic Incremental Model

```sql
{{
    config(
        materialized='incremental',
        unique_key='id',
    )
}}

SELECT
    id,
    city_name,
    temperature_c,
    observation_timestamp
FROM {{ ref('stg_weather_observations') }}

{% if is_incremental() %}
    -- Only new records
    WHERE observation_timestamp > (
        SELECT MAX(observation_timestamp)
        FROM {{ this }}  -- Reference to current table
    )
{% endif %}
```

**First run:** Full table created

**Subsequent runs:** Only new rows added

### Incremental Strategies

**1. Append (default)**
```sql
{{ config(
    materialized='incremental',
    incremental_strategy='append',
) }}

-- Just adds new rows
-- Fast but can create duplicates if not careful
```

**2. Merge (upsert)**
```sql
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='id',
) }}

-- Updates existing rows, inserts new rows
-- Slower but handles updates correctly
```

**3. Delete+Insert**
```sql
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='id',
) }}

-- Deletes matching rows, then inserts
-- Good for partitioned data
```

### Partitioned Incremental

```sql
{{
    config(
        materialized='incremental',
        unique_key='id',
        partition_by={
            'field': 'observation_date',
            'data_type': 'date',
            'granularity': 'day'
        }
    )
}}

SELECT * FROM {{ source('raw', 'observations') }}

{% if is_incremental() %}
    WHERE observation_date >= DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY)
{% endif %}

-- Only processes last 3 days (handles late arrivals)
```

### Full Refresh

Force full rebuild:

```bash
# Rebuild one model
dbt run --select my_incremental_model --full-refresh

# Rebuild all incremental models
dbt run --full-refresh
```

---

## Best Practices

### 1. Naming Conventions

```
Sources:     raw.table_name
Bronze:      stg_source_entity
Silver Fact: fct_subject_event
Silver Dim:  dim_entity
Gold:        agg_grain_subject
Marts:       mrt_audience_subject

Examples:
raw.nightscout_entries
stg_nightscout_glucose_entries
fct_glucose_readings
dim_date
agg_daily_glucose_summary
mrt_patient_glucose_overview
```

### 2. DRY (Don't Repeat Yourself)

**Bad:**
```sql
-- orders_2023.sql
SELECT * FROM raw.orders WHERE YEAR(order_date) = 2023

-- orders_2024.sql
SELECT * FROM raw.orders WHERE YEAR(order_date) = 2024
```

**Good:**
```sql
-- macros/filter_by_year.sql
{% macro filter_by_year(year) %}
    WHERE YEAR(order_date) = {{ year }}
{% endmacro %}

-- orders.sql
SELECT * FROM raw.orders {{ filter_by_year(var('year')) }}
```

### 3. CTEs for Readability

```sql
-- Good: Clear, readable
WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

filtered AS (
    SELECT *
    FROM source
    WHERE order_date >= '2024-01-01'
),

with_metrics AS (
    SELECT
        *,
        amount * 0.1 AS tax,
        amount * 1.1 AS total
    FROM filtered
)

SELECT * FROM with_metrics

-- Bad: Hard to read
SELECT
    *,
    amount * 0.1 AS tax,
    amount * 1.1 AS total
FROM (
    SELECT *
    FROM {{ source('raw', 'orders') }}
    WHERE order_date >= '2024-01-01'
) filtered
```

### 4. Comment Your SQL

```sql
WITH base AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

-- Business rule (2024-06): Exclude cancelled orders per product team
active_orders AS (
    SELECT *
    FROM base
    WHERE status != 'cancelled'
),

-- Calculate lifetime value per customer
-- Uses SUM(amount) not COUNT(*) per analytics team decision
customer_ltv AS (
    SELECT
        customer_id,
        SUM(amount) AS lifetime_value
    FROM active_orders
    GROUP BY customer_id
)

SELECT * FROM customer_ltv
```

### 5. Keep Models Focused

**Bad: One huge model**
```sql
-- orders_with_everything.sql (1000 lines)
WITH orders AS (...),
     customers AS (...),
     products AS (...),
     inventory AS (...),
     shipping AS (...),
     payments AS (...),
     -- Too many concerns!
```

**Good: Separate models**
```
stg_orders.sql
stg_customers.sql
fct_orders.sql  -- Joins orders + customers
fct_inventory.sql  -- Separate concern
```

### 6. Test Everything Important

```yaml
models:
  - name: fct_orders
    tests:
      # Row-level tests
      - dbt_utils.at_least_one

    columns:
      # Key columns
      - name: order_id
        tests:
          - not_null
          - unique

      # Foreign keys
      - name: customer_id
        tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id

      # Business logic
      - name: total_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"  # No negative amounts
```

### 7. Document Important Logic

```yaml
models:
  - name: fct_orders
    description: |
      Orders with calculated metrics and business logic applied.

      **Business Rules:**
      - Excludes cancelled orders (status != 'cancelled')
      - Applies tax rate of 10% (0.1)
      - Free shipping for orders > $100
      - Discount codes applied before tax

      **Data Quality:**
      - Deduplicates on order_id + order_timestamp
      - Filters out test orders (customer_id != 'TEST')
      - Removes orders with negative amounts

      **Refresh Schedule:**
      - Full refresh: Weekly on Sunday
      - Incremental: Hourly
```

### 8. Use Variables for Configuration

**dbt_project.yml:**
```yaml
vars:
  start_date: '2024-01-01'
  tax_rate: 0.1
  free_shipping_threshold: 100
```

**In models:**
```sql
SELECT
    *,
    amount * {{ var('tax_rate') }} AS tax_amount
FROM orders
WHERE order_date >= '{{ var('start_date') }}'
```

### 9. Leverage Tags

```yaml
models:
  bronze:
    +tags: ['bronze', 'staging']

  silver:
    fct_orders:
      +tags: ['silver', 'fact', 'revenue', 'daily']

    dim_customers:
      +tags: ['silver', 'dimension', 'customer']
```

**Run by tag:**
```bash
dbt run --select tag:revenue
dbt test --select tag:critical
```

### 10. Version Control Everything

**.gitignore:**
```
target/
dbt_packages/
logs/
.env
```

**Commit:**
- ✅ Models (.sql)
- ✅ Tests (.yml, .sql)
- ✅ Macros (.sql)
- ✅ Documentation (.yml, .md)
- ✅ Configuration (.yml)
- ❌ Compiled SQL (target/)
- ❌ Packages (dbt_packages/)

---

## Summary

**Key Concepts:**
- **Sources** = External tables
- **Models** = SELECT statements
- **Refs** = Dependencies
- **Tests** = Data quality
- **Docs** = Auto-generated
- **Macros** = Reusable SQL
- **Incremental** = Process only new data

**Common Commands:**
```bash
# Compile (check for errors)
dbt compile

# Run transformations
dbt run

# Run specific model
dbt run --select my_model

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

**Best Practices:**
- ✅ Use naming conventions
- ✅ Keep models focused
- ✅ Use CTEs for readability
- ✅ Comment business logic
- ✅ Test important columns
- ✅ Document everything
- ✅ Use incremental models for large data
- ✅ Version control all code

**Next:** [Troubleshooting Guide](../operations/troubleshooting.md) - Debug common dbt issues.
