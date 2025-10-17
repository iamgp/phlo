{{ config(
    materialized='incremental',
    unique_key='reading_date',
    tags=['nightscout', 'mart']
) }}

/*
Glucose overview mart for BI dashboards

This mart table is incrementally materialized in Iceberg for fast dashboard queries in
Superset. It provides a denormalized, aggregated view optimized for
visualization and reporting.

Target: Iceberg (incrementally updated), then published to PostgreSQL
Refresh: Every 30 minutes via Dagster schedule, only new data
*/

select
    reading_date,
    day_name,
    week_of_year,
    month,
    year,

    -- Daily metrics
    reading_count,
    avg_glucose_mg_dl,
    min_glucose_mg_dl,
    max_glucose_mg_dl,
    stddev_glucose_mg_dl,

    -- Time in range (key diabetes management metric)
    time_in_range_pct,
    time_below_range_pct,
    time_above_range_pct,

    -- Estimated HbA1c (7-day rolling average)
    estimated_a1c_pct,
    avg(estimated_a1c_pct) over (
        order by reading_date
        rows between 6 preceding and current row
    ) as estimated_a1c_7d_avg,

    -- Trend indicators
    avg_glucose_mg_dl - lag(avg_glucose_mg_dl) over (
        order by reading_date
    ) as glucose_change_from_prev_day,

    -- Glucose variability coefficient
    case
        when avg_glucose_mg_dl > 0
        then round(100.0 * stddev_glucose_mg_dl / avg_glucose_mg_dl, 1)
        else null
    end as coefficient_of_variation

from {{ ref('dim_date') }}
where reading_date >= current_date - interval '90' day  -- Last 90 days for dashboard

{% if is_incremental() %}
    -- Only process new dates on incremental runs
    and reading_date >= (select coalesce(max(reading_date), date('1900-01-01')) from {{ this }})
{% endif %}

order by reading_date desc
