-- fct_repository_stats.sql - Silver layer fact table for enriched repository statistics
-- Creates a comprehensive fact table with calculated metrics for repository analytics
-- Transforms raw staging data into analysis-ready format with business logic

{{ config(
    materialized='table',
    tags=['github', 'int']
) }}

/*
Enriched GitHub repository data with calculated metrics

This model adds useful calculated fields:
- Repository age calculations
- Days since last update
- Popularity scoring based on stars, forks, and engagement
- Activity indicators (active in last 30 days)
- Language classification

These enrichments enable better analytics and visualization in downstream models.
*/

-- CTE for source data from bronze layer staging
with repos_data as (
    select * from {{ ref('stg_github_repos') }}
),

-- CTE for current date reference
current_date_ref as (
    select current_date as analysis_date
),

-- CTE for enriched data with calculated fields and business logic
enriched as (
    -- Select statement with field mappings and calculated metrics
    select
        r.repository_id,
        r.repository_name,
        r.repository_full_name,
        r.stars_count,
        r.forks_count,
        r.primary_language,
        r.repository_created_at,
        r.repository_updated_at,

        -- Age and recency calculations
        date_diff(
            'day',
            cast(r.repository_created_at as timestamp),
            c.analysis_date
        ) as repository_age_days,

        date_diff(
            'day',
            cast(r.repository_updated_at as timestamp),
            c.analysis_date
        ) as days_since_last_update,

        -- Popularity score (weighted combination of metrics)
        -- Stars weighted 3x, forks weighted 5x for engagement
        (r.stars_count * 3) + (r.forks_count * 5) as popularity_score,

        -- Activity indicators
        case
            when date_diff(
                'day',
                cast(r.repository_updated_at as timestamp),
                c.analysis_date
            ) <= 30 then 1
            else 0
        end as is_active_last_30d,

        case
            when date_diff(
                'day',
                cast(r.repository_updated_at as timestamp),
                c.analysis_date
            ) <= 90 then 1
            else 0
        end as is_active_last_90d,

        -- Language category for grouping
        coalesce(r.primary_language, 'Unknown') as language_category,

        -- Engagement rate (stars per day of existence)
        case
            when
                date_diff(
                    'day',
                    cast(r.repository_created_at as timestamp),
                    c.analysis_date
                ) > 0
                then cast(r.stars_count as double) / date_diff(
                    'day',
                    cast(r.repository_created_at as timestamp),
                    c.analysis_date
                )
            else 0.0
        end as stars_per_day,

        -- Metadata
        r._phlo_ingested_at

    from repos_data as r
    cross join current_date_ref as c
)

select * from enriched
order by popularity_score desc, repository_updated_at desc
