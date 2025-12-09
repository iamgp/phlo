-- mrt_github_activity_overview.sql - GitHub activity overview mart for BI dashboards in PostgreSQL
-- Incrementally materialized mart providing denormalized daily GitHub activity metrics
-- Optimized for fast dashboard queries and visualization in Superset

{{ config(
    materialized='incremental',
    unique_key='activity_date',
    incremental_strategy='merge',
    schema='marts',
    tags=['github', 'mart']
) }}

/*
GitHub activity overview mart for BI dashboards

This mart table is incrementally materialized in Iceberg for fast dashboard queries in
Superset. It provides a denormalized, aggregated view optimized for
visualization and reporting.

Target: Iceberg (incrementally updated), then published to PostgreSQL
Refresh: Every 6 hours via Dagster schedule, only new data
*/

-- CTE to compute streak groups (avoid nested window functions)
with base_metrics as (
    select
        activity_date,
        day_name,
        week_of_year,
        month,
        year,
        total_events,
        unique_repos_count,
        push_events,
        pr_events,
        issue_events,
        watch_events,
        fork_events,
        code_contribution_events,
        collaboration_events,
        social_events,
        events_per_repo
    from {{ ref('fct_daily_github_metrics') }}
    where
        activity_date >= current_date - interval '90' day

        {% if is_incremental() %}
            and activity_date >= (select coalesce(max(activity_date), date('1900-01-01')) from {{ this }})
        {% endif %}
),

streak_groups as (
    select
        *,
        sum(case when total_events = 0 then 1 else 0 end) over (
            order by activity_date
            rows unbounded preceding
        ) as streak_group
    from base_metrics
)

-- Select statement: Enrich daily GitHub data with rolling averages and trend indicators
select
    activity_date,
    day_name,
    week_of_year,
    month,
    year,

    -- Daily metrics
    total_events,
    unique_repos_count,
    push_events,
    pr_events,
    issue_events,
    watch_events,
    fork_events,

    -- Category metrics
    code_contribution_events,
    collaboration_events,
    social_events,

    -- Contribution intensity
    events_per_repo,

    -- Rolling averages (7-day window)
    cast(avg(total_events) over (
        order by activity_date
        rows between 6 preceding and current row
    ) as double) as total_events_7d_avg,

    cast(avg(push_events) over (
        order by activity_date
        rows between 6 preceding and current row
    ) as double) as push_events_7d_avg,

    cast(avg(unique_repos_count) over (
        order by activity_date
        rows between 6 preceding and current row
    ) as double) as unique_repos_7d_avg,

    -- Trend indicators (day-over-day change)
    total_events - lag(total_events) over (
        order by activity_date
    ) as total_events_change_from_prev_day,

    push_events - lag(push_events) over (
        order by activity_date
    ) as push_events_change_from_prev_day,

    -- Contribution streak (consecutive days with activity)
    case
        when total_events > 0
            then row_number() over (partition by streak_group order by activity_date)
        else 0
    end as streak_length,

    -- Activity level classification
    case
        when total_events >= 20 then 'very_active'
        when total_events >= 10 then 'active'
        when total_events >= 5 then 'moderate'
        when total_events > 0 then 'light'
        else 'inactive'
    end as activity_level

from streak_groups
order by activity_date desc
