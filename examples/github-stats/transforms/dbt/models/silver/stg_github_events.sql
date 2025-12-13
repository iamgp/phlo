{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='event_id',
    on_schema_change='sync_all_columns',
    schema='silver',
    tags=['github', 'stg']
) }}

with raw_data as (
    select * from {{ source('dagster_assets', 'user_events') }}
)

select
    id as event_id,
    type as event_type,
    created_at as event_timestamp,
    actor__login as actor_username,
    repo__name as repository_name,
    _dlt_load_id,
    _dlt_id,
    _phlo_row_id,
    _phlo_ingested_at,
    _phlo_partition_date,
    _phlo_run_id
from raw_data
where
    id is not null
    and type is not null
    and created_at is not null
    {% if var('partition_date_str', None) is not none %}
        and _phlo_partition_date = '{{ var('partition_date_str') }}'
    {% endif %}
