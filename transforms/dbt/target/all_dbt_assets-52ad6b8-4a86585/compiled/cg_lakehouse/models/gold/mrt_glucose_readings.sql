

/*
Curated fact table for glucose readings

This model provides a clean, deduplicated, production-ready dataset for
analytics and reporting. It's incrementally updated to handle new data
efficiently.

Incremental Strategy:
- On first run: processes all historical data
- On subsequent runs: only processes new entries based on reading_timestamp
*/

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

from "memory"."main_silver"."fct_glucose_readings"

