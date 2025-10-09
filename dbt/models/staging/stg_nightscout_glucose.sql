{{ config(
    materialized='view',
    tags=['nightscout', 'stg']
) }}

-- Staging model for Nightscout glucose readings
-- This model reads raw JSONL files from Airbyte and provides a clean,
-- typed view of glucose data. It serves as the foundation for downstream
-- transformations.
-- Source: Airbyte sync from Nightscout API
-- Refresh: On-demand via Dagster

{% set upstream = source('dagster_assets', 'nightscout_entries') %}

with raw_data as (
    select
        _airbyte_ab_id,
        _airbyte_emitted_at,
        _airbyte_data
    from read_json_auto('/data/airbyte/workspace/data/lake/raw/nightscout/_airbyte_raw_nightscout_entries.jsonl')
)

select
    _airbyte_data._id as entry_id,
    _airbyte_data.sgv as glucose_mg_dl,
    epoch_ms(_airbyte_data.date) as reading_timestamp,
    _airbyte_data.dateString as timestamp_iso,
    _airbyte_data.direction,
    _airbyte_data.trend,
    _airbyte_data.device,
    _airbyte_data.type as reading_type,
    _airbyte_data.utcOffset as utc_offset_minutes,
    _airbyte_emitted_at as airbyte_synced_at
from raw_data
where _airbyte_data.sgv is not null
    and _airbyte_data.sgv between 20 and 600  -- Physiologically plausible range
