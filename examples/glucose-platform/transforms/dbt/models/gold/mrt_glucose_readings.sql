-- mrt_glucose_readings.sql - Gold layer curated fact table for glucose readings
-- Provides clean, deduplicated, production-ready glucose data for analytics
-- Incrementally updated to efficiently handle new readings

{{ config(
    materialized='incremental',
   unique_key='entry_id',
    tags=['nightscout', 'curated']
) }}

/*
Curated fact table for glucose readings

This model provides a clean, deduplicated, production-ready dataset for
analytics and reporting. It's incrementally updated to handle new data
efficiently.

Incremental Strategy:
- On first run: processes all historical data
- On subsequent runs: only processes new entries based on reading_timestamp
*/

-- Select statement: Retrieve all enriched glucose reading fields from silver layer
with source_data as (
    select * from {{ ref('fct_glucose_readings') }}
)

select
    source_data.entry_id,
    source_data.glucose_mg_dl,
    source_data.reading_timestamp,
    source_data.reading_date,
    source_data.hour_of_day,
    source_data.day_of_week,
    source_data.day_name,
    source_data.glucose_category,
    source_data.is_in_range,
    source_data.glucose_change_mg_dl,
    source_data.direction,
    source_data.trend,
    source_data.device

from source_data

{% if is_incremental() %}
    -- Only process new data on incremental runs
    where source_data.reading_timestamp > (
        select max(this_table.reading_timestamp)
        from {{ this }} as this_table
    )
{% endif %}
