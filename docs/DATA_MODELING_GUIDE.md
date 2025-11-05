# Data Modeling Guide - Bronze, Silver, Gold Architecture

## Understanding the Medallion Architecture

This guide explains how to design and organize your data using the Bronze/Silver/Gold pattern (also called the Medallion Architecture).

---

## Table of Contents

1. [What is Medallion Architecture?](#what-is-medallion-architecture)
2. [The Bronze Layer](#the-bronze-layer)
3. [The Silver Layer](#the-silver-layer)
4. [The Gold Layer](#the-gold-layer)
5. [The Marts Layer](#the-marts-layer)
6. [Design Principles](#design-principles)
7. [Common Patterns](#common-patterns)
8. [Schema Evolution](#schema-evolution)
9. [Real-World Examples](#real-world-examples)

---

## What is Medallion Architecture?

### The Layers

```
RAW → BRONZE → SILVER → GOLD → MARTS
```

**Purpose of each layer:**

| Layer | Purpose | Who Uses It | Materialization |
|-------|---------|-------------|-----------------|
| **Raw** | Exact copy of source data | Data engineers debugging | Tables |
| **Bronze** | Cleaned, standardized | Data engineers | Tables/Views |
| **Silver** | Business logic applied | Analysts, Data Scientists | Tables |
| **Gold** | Aggregated, conformed | Business users | Tables |
| **Marts** | Published to BI tools | Dashboard consumers | Tables (Postgres) |

###

 Why This Pattern?

**Benefits:**
- ✅ **Reproducibility** - Can always rebuild from raw
- ✅ **Debuggability** - Easy to isolate issues
- ✅ **Flexibility** - Change downstream without reingesting
- ✅ **Performance** - Each layer optimized for its purpose
- ✅ **Governance** - Clear data quality progression

**Real-world analogy:**

Think of it like food processing:
- **Raw**: Fresh ingredients from the farm (messy, varied)
- **Bronze**: Washed and sorted ingredients
- **Silver**: Prepped and measured ingredients
- **Gold**: Cooked dishes
- **Marts**: Plated and ready to serve

---

## The Bronze Layer

### Purpose

The Bronze layer **cleanses and standardizes** raw data without applying business logic.

### What Happens Here

**Type conversions:**
```sql
-- Raw: date stored as bigint (milliseconds)
CAST(date_ms AS TIMESTAMP) AS date_timestamp

-- Raw: numeric stored as string
CAST(value_str AS DOUBLE) AS value_numeric
```

**Standardization:**
```sql
-- Lowercase for consistency
LOWER(TRIM(category)) AS category

-- Standardize nulls
NULLIF(TRIM(field), '') AS field  -- Empty strings → NULL
```

**Column renaming:**
```sql
-- Make names descriptive and consistent
sgv AS glucose_value,
bg AS blood_glucose_mg_dl,
ts AS timestamp_utc
```

**Data cleaning:**
```sql
-- Remove duplicates
SELECT DISTINCT * FROM source

-- Filter invalid records
WHERE created_at IS NOT NULL
  AND id IS NOT NULL
```

### What DOESN'T Happen Here

❌ **NO business logic** (no "is_active", "status_category", etc.)
❌ **NO aggregations** (no GROUP BY)
❌ **NO enrichments** (no calculated fields like "days_since_")
❌ **NO joins** (single-source transformations only)

### Bronze Layer Best Practices

**1. Keep it close to source**
```sql
-- GOOD: Minimal transformation
SELECT
    id,
    CAST(created_at AS TIMESTAMP) AS created_timestamp,
    CAST(amount AS DECIMAL(10,2)) AS amount,
    LOWER(TRIM(status)) AS status
FROM {{ source('raw', 'orders') }}

-- BAD: Too much logic
SELECT
    id,
    created_at,
    amount,
    CASE
        WHEN status = 'completed' AND amount > 100 THEN 'high_value'
        ELSE 'standard'
    END AS order_category  -- This belongs in Silver!
FROM {{ source('raw', 'orders') }}
```

**2. Document all transformations**
```sql
-- Good practice: Comment why you're doing something
SELECT
    id,
    -- Convert Unix milliseconds to timestamp
    CAST(FROM_UNIXTIME(date_ms / 1000) AS TIMESTAMP) AS observation_timestamp,

    -- Standardize missing values: empty strings → NULL
    NULLIF(TRIM(notes), '') AS notes,

    -- Remove leading/trailing whitespace and lowercase
    LOWER(TRIM(city_name)) AS city_name
FROM {{ source('raw', 'observations') }}
```

**3. Filter only technical invalids**
```sql
-- GOOD: Filter technical problems
WHERE id IS NOT NULL  -- Can't process without ID
  AND created_at IS NOT NULL  -- Can't process without timestamp
  AND amount >= 0  -- Negative amounts are data errors

-- BAD: Filter business logic
WHERE status != 'cancelled'  -- This is business logic, belongs in Silver
```

**4. Naming convention**

```
stg_<source>_<entity>

Examples:
- stg_salesforce_accounts
- stg_stripe_payments
- stg_google_analytics_pageviews
- stg_nightscout_glucose_entries
```

---

## The Silver Layer

### Purpose

The Silver layer adds **business logic and context** to create analytics-ready fact and dimension tables.

### What Happens Here

**Calculated fields:**
```sql
-- Business metrics
amount * tax_rate AS tax_amount,
amount + (amount * tax_rate) AS total_amount,

-- Categorizations
CASE
    WHEN amount < 50 THEN 'Low'
    WHEN amount < 200 THEN 'Medium'
    ELSE 'High'
END AS value_category,

-- Indicators
CASE
    WHEN status IN ('completed', 'delivered') THEN TRUE
    ELSE FALSE
END AS is_fulfilled
```

**Enrichments:**
```sql
-- Date parts for easy filtering
DATE(created_timestamp) AS created_date,
YEAR(created_timestamp) AS created_year,
MONTH(created_timestamp) AS created_month,
DAY(created_timestamp) AS created_day,
DAYOFWEEK(created_timestamp) AS day_of_week,

-- Time-based calculations
DATEDIFF(delivered_date, ordered_date) AS delivery_days,
AGE(customer_birthdate, current_date) AS customer_age
```

**Window functions:**
```sql
-- Running totals
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY order_date
) AS cumulative_spend,

-- Rankings
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY order_date
) AS order_number,

-- Moving averages
AVG(amount) OVER (
    ORDER BY order_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
) AS rolling_7day_avg
```

**Joins (denormalization):**
```sql
-- Join related entities for analysis
SELECT
    o.*,
    c.customer_name,
    c.customer_segment,
    p.product_name,
    p.product_category
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('stg_products') }} p ON o.product_id = p.product_id
```

### Fact vs Dimension Tables

**Fact Tables (fct_):**
- Measurements, metrics, transactions
- Grain: One row per event/transaction
- Many rows (millions+)
- Mostly numeric data
- Examples: `fct_orders`, `fct_glucose_readings`, `fct_pageviews`

```sql
-- Example fact table
CREATE TABLE silver.fct_orders AS
SELECT
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    total_amount,
    tax_amount,
    -- Calculated metrics
    quantity * unit_price AS subtotal,
    -- Categories
    CASE WHEN total_amount > 100 THEN 'High Value' ELSE 'Standard' END AS value_tier
FROM {{ ref('stg_orders') }}
```

**Dimension Tables (dim_):**
- Descriptive attributes
- Grain: One row per entity
- Fewer rows (thousands)
- Mostly text data
- Examples: `dim_customers`, `dim_products`, `dim_date`

```sql
-- Example dimension table
CREATE TABLE silver.dim_customers AS
SELECT
    customer_id,
    customer_name,
    email,
    signup_date,
    customer_segment,
    lifetime_value,
    -- Calculated attributes
    DATEDIFF(CURRENT_DATE, signup_date) AS days_as_customer,
    CASE
        WHEN lifetime_value > 1000 THEN 'VIP'
        WHEN lifetime_value > 500 THEN 'Premium'
        ELSE 'Standard'
    END AS customer_tier
FROM {{ ref('stg_customers') }}
```

### Silver Layer Best Practices

**1. Design for analytics**
```sql
-- GOOD: Denormalized, ready for queries
SELECT
    order_id,
    customer_id,
    customer_name,  -- Denormalized from dim_customers
    customer_segment,  -- Denormalized
    product_id,
    product_name,  -- Denormalized from dim_products
    order_amount,
    -- Pre-calculated metrics
    order_amount / NULLIF(total_lifetime_value, 0) AS pct_of_lifetime_value
FROM orders_with_customer_and_product_data

-- BAD: Normalized, requires joins for analysis
SELECT order_id, customer_id, product_id, amount
FROM orders  -- Analyst must join to get customer/product info
```

**2. Document business logic**
```sql
-- GOOD: Clear business rule documentation
-- Business rule (2024-06-01): Orders over $100 get free shipping
CASE
    WHEN order_amount > 100 THEN TRUE
    ELSE FALSE
END AS qualifies_for_free_shipping,

-- Business rule: Customer segments defined by marketing team
CASE
    WHEN total_orders >= 10 AND lifetime_value > 1000 THEN 'VIP'
    WHEN total_orders >= 5 OR lifetime_value > 500 THEN 'Loyal'
    WHEN total_orders >= 2 THEN 'Repeat'
    ELSE 'New'
END AS customer_segment
```

**3. Naming convention**

```
fct_<process>_<event>     -- Fact tables
dim_<entity>              -- Dimension tables

Examples:
Fact Tables:
- fct_order_line_items
- fct_glucose_readings
- fct_website_sessions
- fct_payment_transactions

Dimension Tables:
- dim_customers
- dim_products
- dim_locations
- dim_date
```

---

## The Gold Layer

### Purpose

The Gold layer creates **aggregated, business-ready datasets** optimized for specific use cases.

### What Happens Here

**Aggregations:**
```sql
-- Daily aggregations
SELECT
    DATE(order_timestamp) AS order_date,
    customer_segment,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(order_amount) AS total_revenue,
    AVG(order_amount) AS avg_order_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY order_amount) AS median_order_value
FROM {{ ref('fct_orders') }}
GROUP BY order_date, customer_segment
```

**Rollups:**
```sql
-- Multi-grain aggregations
SELECT
    year,
    quarter,
    month,
    product_category,
    SUM(revenue) AS total_revenue,
    SUM(quantity) AS total_quantity,
    AVG(unit_price) AS avg_unit_price
FROM {{ ref('fct_orders') }}
GROUP BY ROLLUP(year, quarter, month, product_category)
```

**Conformed dimensions:**
```sql
-- Shared dimension across business units
CREATE TABLE gold.dim_date AS
SELECT
    date_key,
    date_actual,
    day_of_week,
    day_name,
    week_of_year,
    month_number,
    month_name,
    quarter,
    year,
    is_weekend,
    is_holiday,
    fiscal_year,
    fiscal_quarter
FROM date_spine
```

**Business metrics:**
```sql
-- KPIs calculated once, used everywhere
SELECT
    customer_id,
    -- Recency, Frequency, Monetary (RFM)
    DATEDIFF(CURRENT_DATE, MAX(order_date)) AS days_since_last_order,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(order_amount) AS lifetime_value,
    AVG(order_amount) AS avg_order_value,
    -- Customer status
    CASE
        WHEN DATEDIFF(CURRENT_DATE, MAX(order_date)) <= 90 THEN 'Active'
        WHEN DATEDIFF(CURRENT_DATE, MAX(order_date)) <= 365 THEN 'At Risk'
        ELSE 'Churned'
    END AS customer_status
FROM {{ ref('fct_orders') }}
GROUP BY customer_id
```

### Gold Layer Best Practices

**1. Design for specific use cases**
```sql
-- GOOD: Purpose-built for executive dashboard
-- Gold table: agg_executive_daily_metrics
SELECT
    report_date,
    total_revenue,
    total_orders,
    new_customers,
    returning_customers,
    avg_order_value,
    revenue_vs_target,
    orders_vs_target
FROM daily_aggregations
WHERE report_date >= CURRENT_DATE - INTERVAL '90' DAY

-- GOOD: Purpose-built for operations team
-- Gold table: agg_hourly_fulfillment_metrics
SELECT
    fulfillment_hour,
    warehouse_id,
    orders_received,
    orders_processed,
    orders_shipped,
    avg_processing_time_minutes,
    pct_shipped_within_sla
FROM hourly_warehouse_stats
```

**2. Pre-calculate expensive computations**
```sql
-- Calculate once in Gold, not every query
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', first_order_date) AS cohort_month
    FROM {{ ref('dim_customers') }}
),
retention AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', o.order_date) AS order_month,
        COUNT(DISTINCT o.customer_id) AS active_customers
    FROM cohorts c
    JOIN {{ ref('fct_orders') }} o ON c.customer_id = o.customer_id
    GROUP BY c.cohort_month, order_month
)
SELECT * FROM retention
```

**3. Naming convention**

```
agg_<grain>_<subject>_<metric>

Examples:
- agg_daily_revenue_by_segment
- agg_weekly_customer_retention
- agg_monthly_product_performance
- agg_hourly_website_traffic
```

---

## The Marts Layer

### Purpose

The Marts layer **publishes** data to BI tools and applications, optimized for specific consumers.

### What Happens Here

**Simplification:**
```sql
-- Remove unnecessary columns
-- Add business-friendly names
-- Pre-filter to relevant data
SELECT
    date AS "Date",
    city_name AS "City",
    avg_temp_c AS "Average Temperature (°C)",
    avg_temp_f AS "Average Temperature (°F)",
    predominant_weather AS "Weather Condition",
    pct_comfortable AS "Comfortable Hours (%)"
FROM {{ ref('agg_daily_weather_summary') }}
WHERE date >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY date DESC
```

**Denormalization:**
```sql
-- Fully denormalized - no joins needed in BI tool
SELECT
    o.order_date,
    o.order_id,
    c.customer_name,
    c.customer_email,
    c.customer_segment,
    p.product_name,
    p.product_category,
    o.quantity,
    o.unit_price,
    o.total_amount,
    w.warehouse_name,
    w.warehouse_region
FROM {{ ref('fct_orders') }} o
LEFT JOIN {{ ref('dim_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('dim_products') }} p ON o.product_id = p.product_id
LEFT JOIN {{ ref('dim_warehouses') }} w ON o.warehouse_id = w.warehouse_id
```

**Performance optimization:**
```sql
-- Published to PostgreSQL for fast BI queries
-- Indexes added on common filter columns
-- Partitioned by date if large
-- Only recent data (e.g., last 2 years)
```

### Marts Layer Best Practices

**1. Design for your BI tool**
```sql
-- GOOD: Tableau-friendly structure
SELECT
    date_key,
    customer_segment,
    product_category,
    SUM(revenue) AS revenue,
    SUM(quantity) AS quantity,
    COUNT(DISTINCT order_id) AS order_count
FROM combined_data
GROUP BY date_key, customer_segment, product_category
-- Tableau will create visualizations by dragging/dropping dimensions

-- BAD: Requires complex calculations in BI tool
SELECT * FROM raw_transaction_data  -- User must aggregate themselves
```

**2. Naming convention**

```
mrt_<audience>_<subject>

Examples:
- mrt_executive_dashboard_daily
- mrt_sales_team_pipeline
- mrt_operations_fulfillment_hourly
- mrt_finance_revenue_summary
```

---

## Design Principles

### Principle 1: Each Layer Has a Clear Purpose

Don't mix concerns:

```sql
-- BAD: Business logic in Bronze
SELECT
    id,
    CASE WHEN status = 'completed' THEN 'success' ELSE 'other' END AS status_category  -- NO!
FROM {{ source('raw', 'orders') }}

-- GOOD: Just standardization
SELECT
    id,
    LOWER(TRIM(status)) AS status
FROM {{ source('raw', 'orders') }}
```

### Principle 2: Progressive Transformation

Each layer should add value:

```
Raw:    {"temp": "98.6", "time": 1699200000}
Bronze: temp_f = 98.6, time = 2023-11-05 14:00:00
Silver: temp_f = 98.6, temp_c = 37.0, is_fever = false
Gold:   daily_avg_temp_c = 36.8, daily_max_temp_c = 37.2
Marts:  "Average Temperature": 36.8°C, "Status": "Normal"
```

### Principle 3: Optimize for Different Users

| Layer | Optimized For | Query Pattern |
|-------|---------------|---------------|
| Bronze | Engineers | Debugging, investigation |
| Silver | Analysts | Exploratory analysis |
| Gold | Business Users | Standard reports |
| Marts | Executives | Dashboards |

### Principle 4: Schema Flexibility

Design schemas to accommodate change:

```sql
-- GOOD: Flexible schema
CREATE TABLE fct_events (
    event_id STRING,
    event_type STRING,
    event_timestamp TIMESTAMP,
    user_id STRING,
    properties MAP<STRING, STRING>,  -- Extensible!
    metadata STRUCT<...>
)

-- BAD: Rigid schema
CREATE TABLE fct_events (
    event_id STRING,
    event_type STRING,
    -- Adding new event properties requires schema change
    property1 STRING,
    property2 STRING
)
```

---

## Common Patterns

### Pattern 1: Slowly Changing Dimensions (SCD)

**Type 1: Overwrite**
```sql
-- Just update the dimension
UPDATE dim_customers
SET email = 'new@email.com'
WHERE customer_id = 123
```

**Type 2: Track history**
```sql
CREATE TABLE dim_customers (
    customer_key INT,  -- Surrogate key
    customer_id INT,   -- Natural key
    customer_name STRING,
    email STRING,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN
)

-- When customer email changes, add new row
INSERT INTO dim_customers VALUES
(456, 123, 'John Doe', 'new@email.com', '2024-11-05', NULL, true)

-- Mark old row as historical
UPDATE dim_customers
SET valid_to = '2024-11-05', is_current = false
WHERE customer_key = 123
```

### Pattern 2: Snapshot Fact Tables

Capture periodic snapshots:

```sql
-- Daily inventory snapshot
SELECT
    snapshot_date,
    product_id,
    quantity_on_hand,
    quantity_reserved,
    quantity_available
FROM inventory_daily_snapshot
WHERE snapshot_date = CURRENT_DATE
```

### Pattern 3: Accumulating Snapshot

Track process milestones:

```sql
-- Order lifecycle
SELECT
    order_id,
    order_date,
    payment_date,
    fulfillment_date,
    shipped_date,
    delivered_date,
    -- Calculate durations
    DATEDIFF(payment_date, order_date) AS days_to_payment,
    DATEDIFF(shipped_date, fulfillment_date) AS days_to_ship,
    DATEDIFF(delivered_date, shipped_date) AS days_in_transit
FROM fct_order_lifecycle
```

### Pattern 4: Event Sourcing

Keep all events, aggregate as needed:

```sql
-- Events table (append-only)
CREATE TABLE fct_user_events (
    event_id STRING,
    user_id STRING,
    event_type STRING,
    event_timestamp TIMESTAMP,
    event_data JSON
)

-- Aggregate to current state
SELECT
    user_id,
    MAX(CASE WHEN event_type = 'profile_updated' THEN event_data['email'] END) AS current_email,
    MAX(CASE WHEN event_type = 'subscription_changed' THEN event_data['plan'] END) AS current_plan
FROM fct_user_events
GROUP BY user_id
```

---

## Schema Evolution

### Adding Columns (Easy)

```sql
-- Iceberg supports adding columns without rewriting
ALTER TABLE silver.fct_orders
ADD COLUMN discount_amount DOUBLE;

-- In dbt, just add to SELECT
SELECT
    *,
    order_amount * discount_rate AS discount_amount  -- New column
FROM {{ ref('stg_orders') }}
```

### Changing Column Types (Medium)

```sql
-- Iceberg can evolve types (widening)
ALTER TABLE silver.fct_orders
ALTER COLUMN quantity TYPE BIGINT;  -- INT → BIGINT ok

-- For narrowing, recreate table
CREATE TABLE silver.fct_orders_v2 AS
SELECT
    order_id,
    CAST(quantity AS INT) AS quantity  -- If you need to narrow
FROM silver.fct_orders;
```

### Renaming Columns (Easy)

```sql
-- Iceberg supports renaming
ALTER TABLE silver.fct_orders
RENAME COLUMN old_name TO new_name;
```

### Removing Columns (Easy)

```sql
-- Iceberg supports dropping columns
ALTER TABLE silver.fct_orders
DROP COLUMN old_column;
```

---

## Real-World Examples

### Example 1: E-Commerce Orders

**Raw → Bronze:**
```sql
-- Bronze: Clean and standardize
SELECT
    order_id,
    CAST(order_timestamp AS TIMESTAMP) AS order_timestamp,
    CAST(customer_id AS STRING) AS customer_id,
    CAST(total_amount AS DECIMAL(10,2)) AS total_amount,
    LOWER(TRIM(status)) AS status
FROM {{ source('raw', 'orders') }}
WHERE order_id IS NOT NULL
```

**Bronze → Silver:**
```sql
-- Silver: Add business logic
SELECT
    order_id,
    order_timestamp,
    customer_id,
    total_amount,
    status,
    -- Calculated fields
    CASE WHEN status IN ('completed', 'delivered') THEN TRUE ELSE FALSE END AS is_fulfilled,
    CASE
        WHEN total_amount < 50 THEN 'Low'
        WHEN total_amount < 200 THEN 'Medium'
        ELSE 'High'
    END AS value_tier,
    -- Date parts
    DATE(order_timestamp) AS order_date,
    YEAR(order_timestamp) AS order_year,
    MONTH(order_timestamp) AS order_month
FROM {{ ref('stg_orders') }}
```

**Silver → Gold:**
```sql
-- Gold: Aggregate
SELECT
    order_date,
    value_tier,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value,
    SUM(CASE WHEN is_fulfilled THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS fulfillment_rate
FROM {{ ref('fct_orders') }}
GROUP BY order_date, value_tier
```

**Gold → Marts:**
```sql
-- Marts: Business-friendly
SELECT
    order_date AS "Date",
    value_tier AS "Order Value",
    total_orders AS "Orders",
    unique_customers AS "Customers",
    total_revenue AS "Revenue",
    avg_order_value AS "Avg Order Value",
    fulfillment_rate AS "Fulfillment Rate (%)"
FROM {{ ref('agg_daily_orders') }}
WHERE order_date >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY order_date DESC
```

---

## Summary

**Bronze Layer:**
- Clean and standardize
- Type conversions, column renaming
- Remove technical invalids
- No business logic

**Silver Layer:**
- Add business logic
- Calculated fields, categorizations
- Fact and dimension tables
- Join related entities

**Gold Layer:**
- Aggregate and rollup
- Business metrics
- Purpose-built datasets
- Conformed dimensions

**Marts Layer:**
- Publish to BI tools
- Denormalized, optimized
- Business-friendly names
- Performance-tuned

**Remember:** Each layer adds value and serves a specific purpose. Don't skip layers or mix concerns!

---

**Next:** [dbt Development Guide](DBT_DEVELOPMENT_GUIDE.md) - Learn advanced dbt techniques for implementing these patterns.
