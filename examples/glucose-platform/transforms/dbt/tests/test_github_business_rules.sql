-- test_github_business_rules.sql - Custom tests for GitHub business rules validation

{% test test_github_contribution_levels(model) %}

    -- Test that contribution level classifications make sense
    -- High contribution should have more contributors than low contribution

    with contribution_levels as (
        select
            contribution_level,
            avg(contributor_count) as avg_contributors,
            count(*) as repo_count
        from {{ model }}
        where collection_date = (select max(collection_date) from {{ model }})
        group by contribution_level
    )
    select * from contribution_levels
    where contribution_level = 'high_contribution' and avg_contributors < 5
       or contribution_level = 'medium_contribution' and avg_contributors >= 10

{% endtest %}

{% test test_github_activity_trends(model) %}

    -- Test that activity scores are generally increasing or stable
    -- Flags repositories with significant negative trends

    with activity_trends as (
        select
            repo_full_name,
            collection_date,
            activity_score,
            lag(activity_score) over (partition by repo_full_name order by collection_date) as prev_score,
            activity_score - lag(activity_score) over (partition by repo_full_name order by collection_date) as score_change
        from {{ model }}
        where collection_date >= current_date - interval '30' day
    )
    select
        repo_full_name,
        collection_date,
        activity_score,
        prev_score,
        score_change
    from activity_trends
    where score_change < -50  -- Significant drop
        and prev_score > 20    -- Was previously active

{% endtest %}
