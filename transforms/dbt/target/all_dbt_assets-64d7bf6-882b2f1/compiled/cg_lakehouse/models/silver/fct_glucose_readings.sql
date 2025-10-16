

/*
Enriched glucose data with calculated metrics

This model adds useful calculated fields:
- Time-based groupings (hour of day, day of week)
- Blood sugar categories (hypoglycemia, in-range, hyperglycemia)
- Rate of change calculations
- Time in range indicators

These enrichments enable better analytics and visualization in downstream models.
*/

with glucose_data as (
    select * from "dbt"."main_bronze"."stg_entries"
),

enriched as (
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
        extract(dow from reading_timestamp) as day_of_week,
        dayname(reading_timestamp) as day_name,

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
        extract(epoch from (
            reading_timestamp - lag(reading_timestamp) over (
                partition by device
                order by reading_timestamp
            )
        )) / 60 as minutes_since_last_reading

    from glucose_data
)

select * from enriched
order by reading_timestamp desc