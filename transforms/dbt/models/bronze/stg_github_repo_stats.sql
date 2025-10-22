-- stg_github_repo_stats.sql - Bronze layer staging model for raw GitHub repository statistics
-- Creates a clean, typed view of raw GitHub repo stats data from Iceberg raw layer
-- Applies basic filtering and type conversions for downstream silver layer transformations

{{ config(
    materialized='view',
    tags=['github', 'stg']
) }}

-- Staging model for GitHub repository statistics
-- This model reads raw data from Iceberg raw layer and provides a clean,
-- typed view of GitHub repository statistics data. It serves as the foundation for downstream
-- transformations.
-- Source: DLT/PyIceberg ingestion into Iceberg raw.repo_stats
-- Refresh: On-demand via Dagster
-- Partitioning: Supports daily partition filtering via partition_date_str variable

-- CTE for raw data source
with raw_data as (
    select * from {{ source('dagster_assets', 'repo_stats') }}
)

-- Final select: Apply field mapping, type conversions, and basic validations
select
    repo_name,
    repo_full_name,
    repo_id,
    collection_date,
    contributors_data,
    commit_activity_data,
    code_frequency_data,
    participation_data,
    _cascade_ingested_at
from raw_data
-- Apply data quality filters
where repo_name is not null
    and repo_full_name is not null
    and collection_date is not null
    {% if var('partition_date_str', None) is not none %}
    -- Filter to partition date when processing partitioned data
    and collection_date = '{{ var('partition_date_str') }}'
    {% endif %}
