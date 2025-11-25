-- mrt_github_repo_insights.sql - GitHub repository insights mart for BI dashboards in PostgreSQL
-- Incrementally materialized mart providing repository performance and health metrics
-- Optimized for fast dashboard queries and repository analytics in Superset

{{ config(
    materialized='incremental',
   unique_key=['repo_full_name', 'collection_date'],
    tags=['github', 'mart']
) }}

 /*
GitHub repository insights mart for BI dashboards

This mart table provides repository-level analytics including contributor patterns,
activity trends, and repository health indicators.

Target: Iceberg (incrementally updated), then published to PostgreSQL
Refresh: Daily via Dagster schedule
*/

-- Select statement: Enrich repository metrics with comparative analytics
select
    repo_full_name,
    repo_name,
    repo_owner,
    collection_date,

    -- Core metrics
    contributor_count,
    total_commits_last_52_weeks,
    net_code_changes,
    weeks_with_activity,
    activity_score,

    -- Repository classification
    case
        when contributor_count >= 10 then 'high_contribution'
        when contributor_count >= 3 then 'medium_contribution'
        when contributor_count >= 1 then 'low_contribution'
        else 'no_contribution'
    end as contribution_level,

    case
        when activity_score >= 100 then 'very_active'
        when activity_score >= 50 then 'active'
        when activity_score >= 10 then 'moderate'
        else 'inactive'
    end as activity_level,

    -- Commit velocity (commits per week)
    case
        when weeks_with_activity > 0
        then round(total_commits_last_52_weeks::decimal / weeks_with_activity, 2)
        else 0
    end as avg_commits_per_week,

    -- Repository health indicators
    case
        when weeks_with_activity >= 26 then 'healthy'  -- Active in last 6 months
        when weeks_with_activity >= 12 then 'stable'
        when weeks_with_activity >= 4 then 'developing'
        else 'dormant'
    end as repository_health,

    -- Comparative metrics (rolling averages)
    avg(contributor_count) over (
        partition by repo_full_name
        order by collection_date
        rows between 6 preceding and current row
    ) as contributor_count_7d_avg,

    avg(activity_score) over (
        partition by repo_full_name
        order by collection_date
        rows between 6 preceding and current row
    ) as activity_score_7d_avg,

    -- Trend indicators
    contributor_count - lag(contributor_count) over (
        partition by repo_full_name
        order by collection_date
    ) as contributor_change,

    activity_score - lag(activity_score) over (
        partition by repo_full_name
        order by collection_date
    ) as activity_change

from {{ ref('mrt_github_repo_metrics') }}

where collection_date >= current_date - interval '90' day  -- Last 90 days

{% if is_incremental() %}
    -- Only process new dates on incremental runs
    and collection_date >= (select coalesce(max(collection_date), date('1900-01-01')) from {{ this }})
{% endif %}

order by collection_date desc, repo_full_name
