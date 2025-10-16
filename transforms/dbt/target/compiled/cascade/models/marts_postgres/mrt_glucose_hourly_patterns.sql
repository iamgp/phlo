

/*
Hourly glucose patterns for time-of-day analysis

This mart aggregates glucose readings by hour of day to identify patterns
like dawn phenomenon, post-meal spikes, and overnight trends.

Target: PostgreSQL
Use case: Heatmaps and time-of-day pattern analysis in Superset
*/

select
    hour_of_day,
    day_of_week,
    day_name,

    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    round(percentile_cont(0.5) within group (order by glucose_mg_dl), 1) as median_glucose_mg_dl,
    round(percentile_cont(0.25) within group (order by glucose_mg_dl), 1) as p25_glucose_mg_dl,
    round(percentile_cont(0.75) within group (order by glucose_mg_dl), 1) as p75_glucose_mg_dl,

    -- Time in range for this hour/day combination
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,

    -- Variability
    round(stddev(glucose_mg_dl), 1) as stddev_glucose_mg_dl

from "ducklake"."main_gold"."mrt_glucose_readings"
where reading_timestamp >= current_timestamp - interval '30 days'
group by hour_of_day, day_of_week, day_name
order by day_of_week, hour_of_day