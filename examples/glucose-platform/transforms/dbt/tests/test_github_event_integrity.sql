-- test_github_event_integrity.sql - Custom test for GitHub event data integrity
-- Ensures that user events and repository events are consistent

{% test test_github_event_integrity(model) %}

    -- Test that events have valid repository references
    -- This test checks that all events reference repositories that exist in our repo stats

    select
        e.event_id,
        e.repo_full_name,
        e.created_at as event_date
    from {{ model }} e
    left join {{ ref('mrt_github_repo_metrics') }} r
        on e.repo_full_name = r.repo_full_name
        and date(e.created_at) = r.collection_date
    where r.repo_full_name is null
        and e.created_at >= current_date - interval '30' day

{% endtest %}
