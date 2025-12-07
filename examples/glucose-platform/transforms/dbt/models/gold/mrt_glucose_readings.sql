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
select
    entry_id,
    glucose_mg_dl,
    reading_timestamp,
    reading_date,
    hour_of_day,
    day_of_week,
    day_name,
    glucose_category,
    is_in_range,
    glucose_change_mg_dl,
    direction,
    trend,
    device

from {{ ref('fct_glucose_readings') }}

{% if is_incremental() %}
    -- Only process new data on incremental runs
    where reading_timestamp > (select max(reading_timestamp) from {{ this }})
{% endif %}
