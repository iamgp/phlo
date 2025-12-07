-- fct_daily_glucose_metrics.sql - Gold layer daily glucose metrics fact table
-- Creates an incrementally updated fact table with daily glucose metrics
-- enabling time-based analysis and trend tracking for diabetes management

{{ config(
    materialized='incremental',
    unique_key='reading_date',
    incremental_strategy='merge',
    tags=['nightscout', 'curated']
) }}

/*
Daily glucose metrics fact table

Provides a daily grain view with key metrics aggregated by day.
Useful for trend analysis and long-term glucose management tracking.
*/

-- Select statement: Aggregate daily glucose metrics and time dimensions
select
    reading_date,
    cast(round(avg(glucose_mg_dl), 1) as double) as avg_glucose_mg_dl,
    cast(round(stddev(glucose_mg_dl), 1) as double) as stddev_glucose_mg_dl,
    cast(round(100.0 * sum(is_in_range) / count(*), 1) as double) as time_in_range_pct,
    cast(round(100.0 * sum(case when glucose_mg_dl < 70 then 1 else 0 end) / count(*), 1) as double)
        as time_below_range_pct,
    cast(round(100.0 * sum(case when glucose_mg_dl > 180 then 1 else 0 end) / count(*), 1) as double)
        as time_above_range_pct,

    -- Daily statistics
    cast(round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as double) as estimated_a1c_pct,
    format_datetime(reading_date, 'EEEE') as day_name,
    day_of_week(reading_date) as day_of_week,
    week(reading_date) as week_of_year,
    month(reading_date) as month,

    -- Time in range metrics (standard: 70-180 mg/dL)
    year(reading_date) as year,
    count(*) as reading_count,
    min(glucose_mg_dl) as min_glucose_mg_dl,

    -- Glucose management indicator (GMI) approximation
    -- GMI = 3.31 + 0.02392 * avg_glucose_mg_dl
    max(glucose_mg_dl) as max_glucose_mg_dl

from {{ ref('fct_glucose_readings') }}

{% if is_incremental() %}
    -- Only process new dates on incremental runs
    where reading_date > (select coalesce(max(prev.reading_date), date('1900-01-01')) from {{ this }} as prev)
{% endif %}

group by reading_date
order by reading_date desc
