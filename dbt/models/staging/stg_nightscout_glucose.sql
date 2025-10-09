{{ config(
    materialized='view',
    tags=['nightscout', 'stg']
) }}

-- Staging model for Nightscout glucose readings
-- This model reads raw Parquet files from the data lake and provides a clean,
-- typed view of glucose data. It serves as the foundation for downstream
-- transformations.
-- Source: /data/lake/raw/nightscout/*.parquet
-- Refresh: Every 30 minutes via Dagster

{% set upstream = source('dagster_assets', 'processed_nightscout_entries') %}

select
    entry_id,
    glucose_mg_dl,
    timestamp as reading_timestamp,
    timestamp_iso,
    direction,
    trend,
    device,
    type as reading_type,
    utc_offset_minutes
from read_parquet('/data/lake/raw/nightscout/*.parquet')
where glucose_mg_dl is not null
    and glucose_mg_dl between 20 and 600  -- Physiologically plausible range
