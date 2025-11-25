-- fct_github_repo_stats.sql - Silver layer fact table for enriched GitHub repository statistics
-- Creates a comprehensive fact table with calculated metrics for repository analytics
-- Transforms raw staging data into analysis-ready format with business logic

{{ config(
   materialized='table',
    tags=['github', 'int']
) }}

 /*
Enriched GitHub repository statistics with calculated metrics

This model adds useful calculated fields:
- Repository metadata and characteristics
- Statistics aggregation and summaries
- Time-based analysis dimensions
- Repository health indicators

These enrichments enable better analytics and visualization in downstream models.
*/

-- CTE for source data from bronze layer staging
with stats_data as (
    select * from {{ ref('stg_github_repo_stats') }}
),

-- CTE for enriched data with calculated fields and business logic
enriched as (
    -- Select statement with field mappings and calculated metrics
    select
        repo_name,
        repo_full_name,
        repo_id,
        collection_date,
        contributors_data,
        commit_activity_data,
        code_frequency_data,
        participation_data,

        -- Extract basic repository information (would be enhanced with repo API data)
        split_part(repo_full_name, '/', 1) as repo_owner,
        split_part(repo_full_name, '/', 2) as repo_short_name,

        -- Contributors statistics summary
        case
            when contributors_data is not null then
                json_array_length(contributors_data)
            else 0
        end as contributor_count,

        -- Commit activity summary (last 52 weeks)
        case
            when commit_activity_data is not null then
                reduce(
                    transform(
                        commit_activity_data,
                        x -> json_extract_scalar(cast(x as varchar), '$.total')
                    ),
                    0,
                    (acc, x) -> acc + cast(coalesce(x, '0') as integer)
                )
            else 0
        end as total_commits_last_52_weeks,

        -- Code frequency summary (additions/deletions)
        case
            when code_frequency_data is not null and json_array_length(code_frequency_data) > 0 then
                transform(
                    code_frequency_data,
                    x -> json_extract_scalar(cast(x as varchar), '$[1]')  -- deletions are at index 1
                )[1]
            else null
        end as net_code_changes,

        -- Weekly activity indicators
        case
            when commit_activity_data is not null then
                json_array_length(commit_activity_data)
            else 0
        end as weeks_with_activity,

        -- Repository activity score (simple heuristic)
        case
            when contributors_data is not null and commit_activity_data is not null then
                json_array_length(contributors_data) * 10 +
                reduce(
                    transform(
                        commit_activity_data,
                        x -> json_extract_scalar(cast(x as varchar), '$.total')
                    ),
                    0,
                    (acc, x) -> acc + cast(coalesce(x, '0') as integer)
                ) / 10
            else 0
        end as activity_score

    from stats_data
)

select * from enriched
order by collection_date desc, repo_full_name
