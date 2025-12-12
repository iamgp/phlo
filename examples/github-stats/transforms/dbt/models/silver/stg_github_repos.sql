{{ config(
    materialized='view',
    schema='silver',
    tags=['github', 'stg']
) }}

with raw_data as (
    select * from {{ source('dagster_assets', 'user_repos') }}
)

select
    id as repository_id,
    name as repository_name,
    full_name as repository_full_name,
    stargazers_count as stars_count,
    forks_count,
    language as primary_language,
    created_at as repository_created_at,
    updated_at as repository_updated_at,
    _dlt_load_id,
    _dlt_id,
    _phlo_ingested_at
from raw_data
where
    id is not null
    and name is not null
    and created_at is not null
    and stargazers_count >= 0
    and forks_count >= 0
    {% if var('partition_date_str', None) is not none %}
        and date(from_iso8601_timestamp(replace(updated_at, ' ', 'T'))) = date('{{ var('partition_date_str') }}')
    {% endif %}
