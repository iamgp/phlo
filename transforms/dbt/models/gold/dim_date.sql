-- dim_date.sql - Gold layer date dimension for glucose analytics
-- Creates an incrementally updated date dimension with daily glucose metrics
-- enabling time-based analysis and trend tracking for diabetes management

{{ config(
    materialized='incremental',
   unique_key='reading_date',
    tags=['nightscout', 'curated']
) }}

 /*
Date dimension for glucose analytics

Provides a daily grain view with key metrics aggregated by day.
Useful for trend analysis and long-term glucose management tracking.
*/

-- Select statement: Aggregate daily glucose metrics and time dimensions
select
    reading_date,
    format_datetime(reading_date, 'EEEE') as day_name,
    day_of_week(reading_date) as day_of_week,
    week(reading_date) as week_of_year,
    month(reading_date) as month,
    year(reading_date) as year,

    -- Daily statistics
    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    min(glucose_mg_dl) as min_glucose_mg_dl,
    max(glucose_mg_dl) as max_glucose_mg_dl,
    round(stddev(glucose_mg_dl), 1) as stddev_glucose_mg_dl,

    -- Time in range metrics (standard: 70-180 mg/dL)
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,
    round(100.0 * sum(case when glucose_mg_dl < 70 then 1 else 0 end) / count(*), 1) as time_below_range_pct,
    round(100.0 * sum(case when glucose_mg_dl > 180 then 1 else 0 end) / count(*), 1) as time_above_range_pct,

    -- Glucose management indicator (GMI) approximation
    -- GMI = 3.31 + 0.02392 * avg_glucose_mg_dl
    round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as estimated_a1c_pct

from {{ ref('fct_glucose_readings') }}

{% if is_incremental() %}
    -- Only process new or updated dates on incremental runs
    where reading_date >= (select coalesce(max(reading_date), date('1900-01-01')) from {{ this }})
{% endif %}

group by reading_date
order by reading_date desc
