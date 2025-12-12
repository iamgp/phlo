-- fct_daily_github_metrics.sql - Gold layer daily GitHub activity metrics fact table
-- Creates an incrementally updated fact table with daily GitHub activity metrics
-- enabling time-based analysis and trend tracking for GitHub contributions

{{ config(
    materialized='incremental',
    unique_key='activity_date',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    schema='gold',
    tags=['github', 'curated']
) }}

/*
Daily GitHub activity metrics fact table

Provides a daily grain view with key metrics aggregated by day.
Useful for trend analysis and long-term contribution tracking.
*/

-- Select statement: Aggregate daily GitHub metrics and time dimensions
select
    event_date as activity_date,
    max(_phlo_partition_date) as _phlo_partition_date,
    day_name,
    day_of_week,
    week_of_year,
    extract(month from event_date) as month,
    extract(year from event_date) as year,

    -- Daily activity statistics
    count(*) as total_events,
    count(distinct repository_name) as unique_repos_count,
    count(distinct actor_username) as unique_contributors_count,

    -- Event type counts
    sum(is_push) as push_events,
    sum(is_pull_request) as pr_events,
    sum(is_issue) as issue_events,
    sum(is_watch) as watch_events,
    sum(is_fork) as fork_events,
    sum(is_create) as create_events,

    -- Category breakdowns
    sum(case when event_category = 'code_contribution' then 1 else 0 end) as code_contribution_events,
    sum(case when event_category = 'collaboration' then 1 else 0 end) as collaboration_events,
    sum(case when event_category = 'social' then 1 else 0 end) as social_events,
    sum(case when event_category = 'documentation' then 1 else 0 end) as documentation_events,

    -- Contribution intensity (events per active repo)
    cast(
        count(*) as double
    ) / nullif(count(distinct repository_name), 0) as events_per_repo,

    -- Most active repository of the day
    max_by(repository_name, is_push) as most_active_repo

from {{ ref('fct_github_events') }}

{% if var('partition_date_str', None) is not none %}
    where _phlo_partition_date = '{{ var('partition_date_str') }}'
{% elif is_incremental() %}
    -- Only process new dates on incremental runs
    where cast(event_date as date) > (select coalesce(max(activity_date), date '1900-01-01') from {{ this }})
{% endif %}

group by
    event_date,
    day_name,
    day_of_week,
    week_of_year
order by activity_date desc
