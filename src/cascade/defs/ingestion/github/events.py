from __future__ import annotations

from dlt.sources.rest_api import rest_api

from cascade.config import config
from cascade.iceberg.schema import GITHUB_USER_EVENTS_SCHEMA
from cascade.ingestion import cascade_ingestion
from cascade.schemas.github import RawGitHubUserEvents


@cascade_ingestion(
    table_name="github_user_events",
    unique_key="id",
    iceberg_schema=GITHUB_USER_EVENTS_SCHEMA,
    validation_schema=RawGitHubUserEvents,
    group="github",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def github_user_events(partition_date: str):
    """
    Ingest GitHub user events using DLT rest_api source.

    Fetches GitHub events for a specific user for a partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Deduplication based on id field (GitHub's unique event ID)
    - Daily partitioning by event date
    - Automatic validation with Pandera schema
    - Branch-aware writes to Iceberg
    - Automatic pagination through GitHub API

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource for GitHub user events, or None if no data
    """
    if not config.github_username:
        raise ValueError("GitHub username not configured")

    headers = {"Accept": "application/vnd.github+json"}
    if config.github_token:
        headers["Authorization"] = f"token {config.github_token}"

    source = rest_api(  # type: ignore[arg-type]
        {
            "client": {
                "base_url": config.github_base_url,
                "headers": headers,
            },
            "resources": [
                {
                    "name": "user_events",
                    "endpoint": {
                        "path": f"users/{config.github_username}/events",
                        "params": {
                            "per_page": 100,
                        },
                        "paginator": {
                            "type": "page_number",
                            "page_param": "page",
                            "total_path": None,
                            "maximum_page": 3,
                        },
                        "data_selector": "$",
                    },
                }
            ],
        }
    )

    return source
