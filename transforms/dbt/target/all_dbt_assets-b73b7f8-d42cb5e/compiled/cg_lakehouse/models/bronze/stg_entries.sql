

-- Staging model for Nightscout glucose readings
-- This model reads raw data from DuckLake bronze layer and provides a clean,
-- typed view of glucose data. It serves as the foundation for downstream
-- transformations.
-- Source: DLT ingestion into DuckLake bronze.entries
-- Refresh: On-demand via Dagster
-- Partitioning: Supports daily partition filtering via partition_date_str variable

with raw_data as (
    select * from "ducklake"."bronze"."entries"
)

select
    _id as entry_id,
    sgv as glucose_mg_dl,
    epoch_ms(date) as reading_timestamp,
    date_string as timestamp_iso,
    direction,
    trend,
    device,
    type as reading_type,
    utc_offset as utc_offset_minutes
from raw_data
where sgv is not null
    and sgv between 20 and 600  -- Physiologically plausible range
    
    -- Filter to partition date when processing partitioned data
    and date_trunc('day', epoch_ms(date)) = '2025-10-05'::DATE
    