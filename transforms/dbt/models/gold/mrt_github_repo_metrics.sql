-- mrt_github_repo_metrics.sql - Gold layer curated fact table for GitHub repository metrics
-- Provides clean, deduplicated, production-ready repository metrics data for analytics
-- Incrementally updated to efficiently handle new statistics

{{ config(
    materialized='incremental',
   unique_key=['repo_full_name', 'collection_date'],
    tags=['github', 'curated']
) }}

/*
Curated fact table for GitHub repository metrics

This model provides a clean, deduplicated, production-ready dataset for
analytics and reporting. It's incrementally updated to handle new data
efficiently.

Incremental Strategy:
- On first run: processes all historical data
- On subsequent runs: only processes new collection dates
*/

-- Select statement: Retrieve all enriched GitHub repository metrics from silver layer
select
    repo_name,
    repo_full_name,
    repo_id,
    repo_owner,
    repo_short_name,
    collection_date,
    contributor_count,
    total_commits_last_52_weeks,
    net_code_changes,
    weeks_with_activity,
    activity_score,
    contributors_data,
    commit_activity_data,
    code_frequency_data,
    participation_data
from {{ ref('fct_github_repo_stats') }}

{% if is_incremental() %}
    -- Only process new data on incremental runs
    where collection_date > (select coalesce(max(prev.collection_date), date('1900-01-01')) from {{ this }} as prev)
{% endif %}

order by collection_date desc, repo_full_name asc
