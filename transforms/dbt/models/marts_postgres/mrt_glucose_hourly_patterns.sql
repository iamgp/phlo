-- mrt_glucose_hourly_patterns.sql - Mart for hourly glucose pattern analysis in PostgreSQL
-- Aggregates glucose readings by hour and day of week for time-of-day trend analysis
-- Enables identification of patterns like dawn phenomenon and post-meal spikes

{{ config(
   materialized='table',
    tags=['nightscout', 'mart']
) }}

/*
Hourly glucose patterns for time-of-day analysis

This mart aggregates glucose readings by hour of day to identify patterns
like dawn phenomenon, post-meal spikes, and overnight trends.

Target: PostgreSQL
Use case: Heatmaps and time-of-day pattern analysis in Superset
*/

-- Select statement: Aggregate glucose metrics by hour and day of week
select
    hour_of_day,
    day_of_week,
    day_name,

    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    round(approx_percentile(glucose_mg_dl, 0.5), 1) as median_glucose_mg_dl,
    round(approx_percentile(glucose_mg_dl, 0.25), 1) as p25_glucose_mg_dl,
    round(approx_percentile(glucose_mg_dl, 0.75), 1) as p75_glucose_mg_dl,

    -- Time in range for this hour/day combination
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,

    -- Variability
    round(stddev(glucose_mg_dl), 1) as stddev_glucose_mg_dl

from {{ ref('mrt_glucose_readings') }}
where reading_timestamp >= current_timestamp - interval '30' day
group by hour_of_day, day_of_week, day_name
order by day_of_week, hour_of_day
