-- fct_repository_languages.sql - Gold layer repository language statistics fact table
-- Creates a fact table with language-level aggregations for repository analytics
-- enabling language distribution analysis and preference tracking

{{ config(
    materialized='table',
    tags=['github', 'curated']
) }}

/*
Repository language statistics fact table

Provides language-level aggregations showing:
- Repository counts per language
- Engagement metrics (stars, forks) per language
- Activity indicators per language
- Language distribution percentages

Useful for understanding technology preferences and engagement patterns.
*/

-- CTE for language aggregations
with language_stats as (
    select
        language_category,
        count(*) as repository_count,
        sum(stars_count) as total_stars,
        sum(forks_count) as total_forks,
        cast(avg(stars_count) as double) as avg_stars_per_repo,
        cast(avg(forks_count) as double) as avg_forks_per_repo,
        sum(popularity_score) as total_popularity_score,
        sum(is_active_last_30d) as active_repos_last_30d,
        sum(is_active_last_90d) as active_repos_last_90d,
        cast(avg(repository_age_days) as double) as avg_repo_age_days,
        max(stars_count) as max_stars_in_language,
        max_by(repository_name, stars_count) as most_starred_repo
    from {{ ref('fct_repository_stats') }}
    group by language_category
),

-- CTE for total calculations for percentage calculations
totals as (
    select
        sum(repository_count) as total_repos,
        sum(total_stars) as total_stars_all,
        sum(total_forks) as total_forks_all
    from language_stats
)

-- Final select with percentages
select
    l.language_category as primary_language,
    l.repository_count,
    l.total_stars,
    l.total_forks,
    l.avg_stars_per_repo,
    l.avg_forks_per_repo,
    l.total_popularity_score,
    l.active_repos_last_30d,
    l.active_repos_last_90d,
    l.avg_repo_age_days,
    l.max_stars_in_language,
    l.most_starred_repo,

    -- Percentage distributions
    cast(
        round(100.0 * l.repository_count / nullif(t.total_repos, 0), 2)
        as double
    ) as repo_count_pct,

    cast(
        round(100.0 * l.total_stars / nullif(t.total_stars_all, 0), 2)
        as double
    ) as star_pct,

    cast(
        round(100.0 * l.total_forks / nullif(t.total_forks_all, 0), 2)
        as double
    ) as fork_pct,

    -- Engagement ratio (stars per fork)
    cast(
        l.total_stars as double
    ) / nullif(l.total_forks, 0) as stars_per_fork_ratio

from language_stats as l
cross join totals as t
order by l.total_popularity_score desc, l.repository_count desc
