from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import dlt
import requests

from cascade.config import config
from cascade.ingestion import cascade_ingestion
from cascade.schemas.github import RawGitHubRepoStats


@dlt.resource(name="repo_stats", write_disposition="replace")
def fetch_repo_stats(partition_date: str) -> Any:
    """
    DLT resource to fetch GitHub repository statistics.

    Fetches repository list, then retrieves statistics for each repo:
    - Contributors
    - Commit activity
    - Code frequency
    - Participation

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Yields:
        Repository statistics dictionaries
    """
    if not config.github_username:
        raise ValueError("GitHub username not configured")

    headers = {"Accept": "application/vnd.github+json"}
    if config.github_token:
        headers["Authorization"] = f"token {config.github_token}"

    repos_url = f"{config.github_base_url}/users/{config.github_username}/repos"
    repos_response = requests.get(repos_url, headers=headers, timeout=30)
    repos_response.raise_for_status()
    repos = repos_response.json()

    stat_types = [
        ("contributors", "stats/contributors"),
        ("commit_activity", "stats/commit_activity"),
        ("code_frequency", "stats/code_frequency"),
        ("participation", "stats/participation"),
    ]

    for repo in repos:
        repo_name = repo["name"]
        repo_full_name = repo["full_name"]

        repo_stats = {
            "repo_name": repo_name,
            "repo_full_name": repo_full_name,
            "repo_id": repo["id"],
            "collection_date": partition_date,
            "_cascade_ingested_at": datetime.now(timezone.utc),
        }

        for stat_type, endpoint in stat_types:
            try:
                stat_url = f"{config.github_base_url}/repos/{repo_full_name}/{endpoint}"
                stat_response = requests.get(stat_url, headers=headers, timeout=60)

                if stat_response.status_code == 202:
                    continue
                elif stat_response.status_code == 204:
                    continue

                stat_response.raise_for_status()
                stat_data = stat_response.json()

                if stat_data:
                    repo_stats[f"{stat_type}_data"] = stat_data

            except requests.HTTPError:
                continue
            except Exception:
                continue

        yield repo_stats


@cascade_ingestion(
    table_name="github_repo_stats",
    unique_key="_dlt_id",
    validation_schema=RawGitHubRepoStats,
    group="github",
    cron="0 2 * * *",
    freshness_hours=(24, 48),
    max_runtime_seconds=600,
    retry_delay_seconds=60,
)
def github_repo_stats(partition_date: str):
    """
    Ingest GitHub repository statistics using custom DLT resource.

    Fetches repository statistics for all user repos for a partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Deduplication based on _dlt_id field (DLT-generated unique ID)
    - Daily partitioning by collection date
    - Multiple stat types: contributors, commit_activity, code_frequency, participation
    - Automatic validation with Pandera schema
    - Branch-aware writes to Iceberg

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource for GitHub repo stats, or None if no data
    """
    return fetch_repo_stats(partition_date)
