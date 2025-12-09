-- mrt_contribution_patterns.sql - Mart for hourly contribution pattern analysis in PostgreSQL
-- Aggregates GitHub events by hour and day of week for time-of-day trend analysis
-- Enables identification of contribution patterns and typical working hours

{{ config(
    materialized='table',
    schema='marts',
    tags=['github', 'mart']
) }}

/*
Hourly contribution patterns for time-of-day analysis

This mart aggregates GitHub events by hour of day and day of week to identify patterns
like typical working hours, weekend activity, and peak contribution times.

Target: PostgreSQL
Use case: Heatmaps and time-of-day pattern analysis in Superset
*/

-- Select statement: Aggregate GitHub activity metrics by hour and day of week
select
    hour_of_day,
    day_of_week,
    day_name,

    count(*) as total_events,
    count(distinct event_date) as days_with_activity,
    count(distinct repository_name) as unique_repos,

    -- Event type breakdowns
    sum(is_push) as push_events,
    sum(is_pull_request) as pr_events,
    sum(is_issue) as issue_events,
    sum(is_watch) as watch_events,
    sum(is_fork) as fork_events,

    -- Category breakdowns
    sum(case when event_category = 'code_contribution' then 1 else 0 end) as code_contribution_events,
    sum(case when event_category = 'collaboration' then 1 else 0 end) as collaboration_events,
    sum(case when event_category = 'social' then 1 else 0 end) as social_events,

    -- Average events per active day in this time slot
    cast(
        count(*) as double
    ) / nullif(count(distinct event_date), 0) as avg_events_per_day,

    -- Activity intensity score (normalized to 0-100 scale)
    cast(
        100.0 * count(*) / nullif(max(count(*)) over (), 0)
        as double
    ) as intensity_score

from {{ ref('fct_github_events') }}
where cast(event_timestamp as timestamp) >= current_timestamp - interval '90' day
group by hour_of_day, day_of_week, day_name
order by day_of_week, hour_of_day
