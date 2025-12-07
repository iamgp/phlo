-- stg_github_user_events.sql - Bronze layer staging model for raw GitHub user events
-- Creates a clean, typed view of raw GitHub event data from Iceberg raw layer
-- Applies basic filtering and type conversions for downstream silver layer transformations

{{ config(
    materialized='view',
    tags=['github', 'stg']
) }}

-- Staging model for GitHub user events
-- This model reads raw data from Iceberg raw layer and provides a clean,
-- typed view of GitHub event data. It serves as the foundation for downstream
-- transformations.
-- Source: DLT/PyIceberg ingestion into Iceberg raw.user_events
-- Refresh: On-demand via Dagster
-- Partitioning: Supports daily partition filtering via partition_date_str variable

-- CTE for raw data source
with raw_data as (
    select * from {{ source('dagster_assets', 'user_events') }}
)

-- Final select: Apply field mapping, type conversions, and basic validations
select
    id as event_id,
    type as event_type,
    actor,
    repo,
    payload,
    public,
    created_at,
    org,
    _cascade_ingested_at
from raw_data
-- Apply data quality filters
where
    id is not null
    and type is not null
    and created_at is not null
    {% if var('partition_date_str', None) is not none %}
    -- Filter to partition date when processing partitioned data
        and date(created_at) = date('{{ var('partition_date_str') }}')
    {% endif %}
