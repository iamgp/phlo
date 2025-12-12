-- mrt_language_distribution.sql - Mart for language distribution analysis in PostgreSQL
-- Aggregates repository statistics by primary language for technology preference analysis
-- Enables visualization of language usage, popularity, and engagement patterns

{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['primary_language', '_phlo_partition_date'],
    on_schema_change='sync_all_columns',
    schema='marts',
    tags=['github', 'mart']
) }}

/*
Language distribution and engagement metrics

This mart provides language-level statistics showing:
- Repository counts per language
- Engagement metrics (stars, forks) per language
- Activity indicators and age metrics
- Distribution percentages for visualization

Target: PostgreSQL
Use case: Language distribution charts, technology stack analysis in Superset
*/

-- Select statement: Present language statistics in dashboard-ready format
select
    primary_language,
    _phlo_partition_date,
    repository_count,
    total_stars,
    total_forks,
    cast(avg_stars_per_repo as decimal(10, 2)) as avg_stars_per_repo,
    cast(avg_forks_per_repo as decimal(10, 2)) as avg_forks_per_repo,
    total_popularity_score,

    -- Activity metrics
    active_repos_last_30d,
    active_repos_last_90d,
    cast(avg_repo_age_days as decimal(10, 1)) as avg_repo_age_days,

    -- Top repository in this language
    max_stars_in_language,
    most_starred_repo,

    -- Distribution percentages (for pie charts and visualizations)
    cast(repo_count_pct as decimal(5, 2)) as repo_count_pct,
    cast(star_pct as decimal(5, 2)) as star_pct,
    cast(fork_pct as decimal(5, 2)) as fork_pct,

    -- Engagement ratio (stars per fork)
    cast(stars_per_fork_ratio as decimal(10, 2)) as stars_per_fork_ratio,

    -- Activity rate (percentage of repos active in last 30 days)
    cast(
        100.0 * active_repos_last_30d / nullif(repository_count, 0)
        as decimal(5, 2)
    ) as active_repos_pct,

    -- Rank by popularity
    row_number() over (order by total_popularity_score desc) as popularity_rank

from {{ ref('fct_repository_languages') }}
{% if var('partition_date_str', None) is not none %}
    where _phlo_partition_date = '{{ var('partition_date_str') }}'
{% endif %}
order by total_popularity_score desc, repository_count desc
