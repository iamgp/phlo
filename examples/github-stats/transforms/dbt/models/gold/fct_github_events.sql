{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='event_id',
    on_schema_change='sync_all_columns',
    schema='gold',
    tags=['github', 'int']
) }}

with events_data as (
    select * from {{ ref('stg_github_events') }}
    {% if var('partition_date_str', None) is not none %}
        where _phlo_partition_date = '{{ var('partition_date_str') }}'
    {% endif %}
),

typed as (
    select
        *,
        cast(from_iso8601_timestamp(replace(event_timestamp, ' ', 'T')) as timestamp(6)) as event_ts
    from events_data
),

enriched as (
    select
        event_id,
        event_type,
        event_timestamp,
        actor_username,
        repository_name,
        date_trunc('day', event_ts) as event_date,
        extract(hour from event_ts) as hour_of_day,
        day_of_week(event_ts) as day_of_week,
        format_datetime(event_ts, 'EEEE') as day_name,
        week_of_year(event_ts) as week_of_year,
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
        _phlo_row_id,
        _phlo_ingested_at,
        _phlo_partition_date,
        _phlo_run_id
    from typed
)

select
    event_id,
    event_type,
    event_timestamp,
    actor_username,
    repository_name,
    event_date,
    hour_of_day,
    day_of_week,
    day_name,
    week_of_year,
    event_category,
    is_push,
    is_pull_request,
    is_issue,
    is_watch,
    is_fork,
    is_create,
    _phlo_row_id,
    _phlo_ingested_at,
    _phlo_partition_date,
    _phlo_run_id
from enriched
order by event_timestamp desc
