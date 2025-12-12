{{ config(
    materialized='view',
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
    _dlt_id
from raw_data
where
    id is not null
    and login is not null
    and followers >= 0
    and following >= 0
    and public_repos >= 0
