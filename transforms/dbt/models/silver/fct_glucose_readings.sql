-- fct_glucose_readings.sql - Silver layer fact table for enriched glucose readings
-- Creates a comprehensive fact table with calculated metrics for diabetes analytics
-- Transforms raw staging data into analysis-ready format with business logic

{{ config(
   materialized='table',
    tags=['nightscout', 'int']
) }}

/*
Enriched glucose data with calculated metrics

This model adds useful calculated fields:
- Time-based groupings (hour of day, day of week)
- Blood sugar categories (hypoglycemia, in-range, hyperglycemia)
- Rate of change calculations
- Time in range indicators

These enrichments enable better analytics and visualization in downstream models.
*/

-- CTE for source data from bronze layer staging
with glucose_data as (
    select * from {{ ref('stg_glucose_entries') }}
),

-- CTE for enriched data with calculated fields and business logic
enriched as (
    -- Select statement with field mappings and calculated metrics
    select
        entry_id,
        glucose_mg_dl,
        reading_timestamp,
        timestamp_iso,
        direction,
        trend,
        device,

        -- Time-based dimensions for analysis
        date_trunc('day', reading_timestamp) as reading_date,
        extract(hour from reading_timestamp) as hour_of_day,
        day_of_week(reading_timestamp) as day_of_week,
        format_datetime(reading_timestamp, 'EEEE') as day_name,

        -- Blood sugar categories (based on ADA guidelines)
        case
            when glucose_mg_dl < 70 then 'hypoglycemia'
            when glucose_mg_dl >= 70 and glucose_mg_dl <= 180 then 'in_range'
            when glucose_mg_dl > 180 and glucose_mg_dl <= 250 then 'hyperglycemia_mild'
            when glucose_mg_dl > 250 then 'hyperglycemia_severe'
        end as glucose_category,

        -- Time in range flag (70-180 mg/dL)
        case
            when glucose_mg_dl >= 70 and glucose_mg_dl <= 180 then 1
            else 0
        end as is_in_range,

        -- Rate of change calculation (lag over 5 minutes)
        glucose_mg_dl - lag(glucose_mg_dl) over (
            partition by device
            order by reading_timestamp
        ) as glucose_change_mg_dl,

        -- Minutes since previous reading
        date_diff(
            'minute',
            lag(reading_timestamp) over (
                partition by device
                order by reading_timestamp
            ),
            reading_timestamp
        ) as minutes_since_last_reading

    from glucose_data
)

select * from enriched
order by reading_timestamp desc
