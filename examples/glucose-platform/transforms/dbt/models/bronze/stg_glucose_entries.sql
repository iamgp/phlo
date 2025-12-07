-- stg_glucose_entries.sql - Bronze layer staging model for raw Nightscout glucose entries
-- Creates a clean, typed view of raw glucose data from Iceberg raw layer
-- Applies basic filtering and type conversions for downstream silver layer transformations

{{ config(
    materialized='view',
    tags=['nightscout', 'stg']
) }}

-- Staging model for Nightscout glucose readings
-- This model reads raw data from Iceberg raw layer and provides a clean,
-- typed view of glucose data. It serves as the foundation for downstream
-- transformations.
-- Source: DLT/PyIceberg ingestion into Iceberg raw.entries
-- Refresh: On-demand via Dagster
-- Partitioning: Supports daily partition filtering via partition_date_str variable

-- CTE for raw data source
with raw_data as (
    select * from {{ source('dagster_assets', 'glucose_entries') }}
)

-- Final select: Apply field mapping, type conversions, and basic validations
-- noqa: disable=ST06
select
    -- Simple columns first
    _id as entry_id,
    sgv as glucose_mg_dl,
    date_string as timestamp_iso,
    direction,
    trend,
    device,
    type as reading_type,
    utc_offset as utc_offset_minutes,
    -- Calculated columns
    coalesce(date_string, from_unixtime(cast(date as double) / 1000.0))
        as reading_timestamp,
    -- Metadata columns
    sys_time,
    sys_time as _phlo_ingested_at,  -- Use sys_time as proxy for ingestion timestamp
    _dlt_load_id,
    _dlt_id
from raw_data
-- Apply data quality filters
where
    sgv is not null
    and sgv between 20 and 600  -- Physiologically plausible range
    {% if var('partition_date_str', None) is not none %}
    -- Filter to partition date when processing partitioned data
        and date(
            coalesce(date_string, from_unixtime(cast(date as double) / 1000.0))
        ) = date('{{ var('partition_date_str') }}')
    {% endif %}
