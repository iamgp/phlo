{{ config(
    materialized='table',
    tags=['github', 'int']
) }}

with events_data as (
    select * from {{ ref('stg_github_events') }}
),

enriched as (
    select
        event_id,
        event_type,
        event_timestamp,
        actor_username,
        repository_name,
        date_trunc('day', cast(event_timestamp as timestamp)) as event_date,
        extract(hour from cast(event_timestamp as timestamp)) as hour_of_day,
        day_of_week(cast(event_timestamp as timestamp)) as day_of_week,
        format_datetime(cast(event_timestamp as timestamp), 'EEEE') as day_name,
        week_of_year(cast(event_timestamp as timestamp)) as week_of_year,
        case
            when event_type in ('PushEvent', 'CreateEvent', 'DeleteEvent') then 'code_contribution'
            when event_type in ('PullRequestEvent', 'PullRequestReviewEvent', 'PullRequestReviewCommentEvent', 'IssuesEvent', 'IssueCommentEvent') then 'collaboration'
            when event_type in ('WatchEvent', 'ForkEvent', 'ReleaseEvent') then 'social'
            when event_type in ('GollumEvent', 'CommitCommentEvent') then 'documentation'
            else 'other'
        end as event_category,
        case when event_type = 'PushEvent' then 1 else 0 end as is_push,
        case when event_type = 'PullRequestEvent' then 1 else 0 end as is_pull_request,
        case when event_type = 'IssuesEvent' then 1 else 0 end as is_issue,
        case when event_type = 'WatchEvent' then 1 else 0 end as is_watch,
        case when event_type = 'ForkEvent' then 1 else 0 end as is_fork,
        case when event_type = 'CreateEvent' then 1 else 0 end as is_create,
        _phlo_ingested_at
    from events_data
)

select * from enriched
order by event_timestamp desc
