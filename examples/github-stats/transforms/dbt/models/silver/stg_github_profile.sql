{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['user_id', '_phlo_partition_date'],
    on_schema_change='sync_all_columns',
    schema='silver',
    tags=['github', 'stg']
) }}

with raw_data as (
    select * from {{ source('dagster_assets', 'user_profile') }}
)

select
    id as user_id,
    login as username,
    name as display_name,
    followers as followers_count,
    following as following_count,
    public_repos as public_repos_count,
    created_at as account_created_at,
    _dlt_load_id,
    _dlt_id,
    _phlo_row_id,
    _phlo_ingested_at,
    _phlo_partition_date,
    _phlo_run_id
from raw_data
where
    id is not null
    and login is not null
    and followers >= 0
    and following >= 0
    and public_repos >= 0
    {% if var('partition_date_str', None) is not none %}
        and _phlo_partition_date = '{{ var('partition_date_str') }}'
    {% endif %}
