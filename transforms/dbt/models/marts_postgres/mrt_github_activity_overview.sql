-- mrt_github_activity_overview.sql - GitHub activity overview mart for BI dashboards in PostgreSQL
-- Incrementally materialized mart providing denormalized daily GitHub activity metrics
-- Optimized for fast dashboard queries and visualization in Superset

{{ config(
    materialized='incremental',
   unique_key='activity_date',
    tags=['github', 'mart']
) }}

 /*
GitHub activity overview mart for BI dashboards

This mart table is incrementally materialized in Iceberg for fast dashboard queries in
Superset. It provides a denormalized, aggregated view optimized for
visualization and reporting.

Target: Iceberg (incrementally updated), then published to PostgreSQL
Refresh: Every 30 minutes via Dagster schedule, only new data
*/

-- Select statement: Enrich daily GitHub activity data with rolling averages and trend indicators
select
    event_date as activity_date,
    day_name,
    week_of_year,
    month,
    year,

    -- Daily activity metrics
    event_count,
    unique_repos_count,
    unique_actors_count,
    public_events_count,
    private_events_count,

    -- Event type breakdown
    code_contribution_events,
    issue_management_events,
    pull_request_events,
    repository_management_events,
    social_events,

    -- Time distribution
    avg_events_per_hour,
    peak_activity_hour,
    events_during_work_hours,

    -- Rolling averages (7-day)
    avg(event_count) over (
        order by event_date
        rows between 6 preceding and current row
    ) as event_count_7d_avg,

    -- Trend indicators
    event_count - lag(event_count) over (
        order by event_date
    ) as event_change_from_prev_day,

    -- Activity diversity score (simple measure of engagement)
    case
        when unique_actors_count > 0
        then round(unique_repos_count::decimal / unique_actors_count, 2)
        else 0
    end as activity_diversity_score

from (
    select
        event_date,
        format_datetime(event_date, 'EEEE') as day_name,
        week(event_date) as week_of_year,
        month(event_date) as month,
        year(event_date) as year,

        -- Basic counts
        count(*) as event_count,
        count(distinct repo_full_name) as unique_repos_count,
        count(distinct actor_login) as unique_actors_count,
        count(*) filter (where public = true) as public_events_count,
        count(*) filter (where public = false) as private_events_count,

        -- Event category counts
        count(*) filter (where event_category = 'code_contribution') as code_contribution_events,
        count(*) filter (where event_category = 'issue_management') as issue_management_events,
        count(*) filter (where event_category = 'pull_request') as pull_request_events,
        count(*) filter (where event_category = 'repository_management') as repository_management_events,
        count(*) filter (where event_category = 'social') as social_events,

        -- Time-based metrics
        round(avg(hour_of_day), 1) as avg_events_per_hour,
        mode() within group (order by hour_of_day) as peak_activity_hour,
        count(*) filter (where hour_of_day between 9 and 17) as events_during_work_hours

    from {{ ref('mrt_github_user_activity') }}
    group by event_date
) daily_metrics

where activity_date >= current_date - interval '90' day  -- Last 90 days for dashboard

{% if is_incremental() %}
    -- Only process new dates on incremental runs
    and activity_date >= (select coalesce(max(activity_date), date('1900-01-01')) from {{ this }})
{% endif %}

order by activity_date desc
