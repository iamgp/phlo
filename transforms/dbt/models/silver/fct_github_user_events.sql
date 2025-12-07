-- fct_github_user_events.sql - Silver layer fact table for enriched GitHub user events
-- Creates a comprehensive fact table with calculated metrics for GitHub analytics
-- Transforms raw staging data into analysis-ready format with business logic

{{ config(
   materialized='table',
    tags=['github', 'int']
) }}

/*
Enriched GitHub user events with calculated metrics

This model adds useful calculated fields:
- Time-based groupings (hour of day, day of week)
- Event categorization and analysis fields
- Actor and repository extracted information
- Event type classifications

These enrichments enable better analytics and visualization in downstream models.
*/

-- CTE for source data from bronze layer staging
with events_data as (
    select * from {{ ref('stg_github_user_events') }}
),

-- CTE for enriched data with calculated fields and business logic
enriched as (
    -- Select statement with field mappings and calculated metrics
    select
        event_id,
        event_type,
        actor,
        repo,
        payload,
        public,
        created_at,
        org,

        -- Time-based dimensions for analysis
        date_trunc('day', created_at) as event_date,
        extract(hour from created_at) as hour_of_day,
        day_of_week(created_at) as day_of_week,
        format_datetime(created_at, 'EEEE') as day_name,

        -- Extract key information from JSON fields (using JSON functions)
        json_extract_string(actor, '$.login') as actor_login,
        json_extract_string(actor, '$.id') as actor_id,
        json_extract_string(repo, '$.name') as repo_name,
        json_extract_string(repo, '$.full_name') as repo_full_name,

        -- Event type categorization
        case
            when event_type in ('PushEvent', 'CommitCommentEvent') then 'code_contribution'
            when event_type in ('IssuesEvent', 'IssueCommentEvent') then 'issue_management'
            when
                event_type in ('PullRequestEvent', 'PullRequestReviewEvent', 'PullRequestReviewCommentEvent')
                then 'pull_request'
            when event_type in ('CreateEvent', 'DeleteEvent', 'ForkEvent') then 'repository_management'
            when event_type = 'WatchEvent' then 'social'
            when event_type = 'MemberEvent' then 'collaboration'
            when event_type = 'ReleaseEvent' then 'release_management'
            when event_type = 'GollumEvent' then 'documentation'
            when event_type = 'PublicEvent' then 'visibility'
            else 'other'
        end as event_category,

        -- Repository visibility (public/private)
        not coalesce(json_extract_string(repo, '$.private') = 'true', false) as is_repo_public,

        -- Organization involvement
        coalesce(org is not null, false) as involves_organization

    from events_data
)

select * from enriched
order by created_at desc
