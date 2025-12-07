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
with source_data as (
    select * from {{ ref('fct_glucose_readings') }}
)
-- noqa: disable=ST06
select
    -- Simple dimensions first
    source_data.reading_date,
    -- Derived dimensions (calculations on dimensions)
    format_datetime(source_data.reading_date, 'EEEE') as day_name,
    day_of_week(source_data.reading_date) as day_of_week,
    week(source_data.reading_date) as week_of_year,
    month(source_data.reading_date) as month,
    year(source_data.reading_date) as year,

    -- Aggregated metrics
    count(*) as reading_count,
    cast(round(avg(source_data.glucose_mg_dl), 1) as double) as avg_glucose_mg_dl,
    min(source_data.glucose_mg_dl) as min_glucose_mg_dl,
    max(source_data.glucose_mg_dl) as max_glucose_mg_dl,
    cast(round(stddev(source_data.glucose_mg_dl), 1) as double) as stddev_glucose_mg_dl,

    -- Time in range metrics (standard: 70-180 mg/dL)
    cast(
        round(100.0 * sum(source_data.is_in_range) / count(*), 1) as double
    ) as time_in_range_pct,
    cast(
        round(
            100.0 * sum(case when source_data.glucose_mg_dl < 70 then 1 else 0 end)
            / count(*), 1
        ) as double
    ) as time_below_range_pct,
    cast(
        round(
            100.0 * sum(case when source_data.glucose_mg_dl > 180 then 1 else 0 end)
            / count(*), 1
        ) as double
    ) as time_above_range_pct,

    -- Glucose management indicator (GMI) approximation
    -- GMI = 3.31 + 0.02392 * avg_glucose_mg_dl
    cast(
        round(3.31 + (0.02392 * avg(source_data.glucose_mg_dl)), 2) as double
    ) as estimated_a1c_pct

from source_data

{% if is_incremental() %}
    -- Only process new dates on incremental runs
    where source_data.reading_date > (
        select coalesce(max(this_table.reading_date), date('1900-01-01'))
        from {{ this }} as this_table
    )
{% endif %}

group by source_data.reading_date
order by source_data.reading_date desc
