-- mrt_github_user_activity.sql - Gold layer curated fact table for GitHub user activity
-- Provides clean, deduplicated, production-ready GitHub activity data for analytics
-- Incrementally updated to efficiently handle new events

{{ config(
    materialized='incremental',
   unique_key='event_id',
    tags=['github', 'curated']
) }}

/*
Curated fact table for GitHub user activity

This model provides a clean, deduplicated, production-ready dataset for
analytics and reporting. It's incrementally updated to handle new data
efficiently.

Incremental Strategy:
- On first run: processes all historical data
- On subsequent runs: only processes new events based on created_at
*/

-- Select statement: Retrieve all enriched GitHub user activity fields from silver layer
select
    event_id,
    event_type,
    event_category,
    actor_login,
    actor_id,
    repo_name,
    repo_full_name,
    public,
    is_repo_public,
    involves_organization,
    created_at,
    event_date,
    hour_of_day,
    day_of_week,
    day_name,
    org
from {{ ref('fct_github_user_events') }}

{% if is_incremental() %}
    -- Only process new data on incremental runs
    where created_at > (select max(prev.created_at) from {{ this }} as prev)
{% endif %}
