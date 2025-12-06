"""Github user_profile ingestion asset."""

from __future__ import annotations

import os

from dlt.sources.rest_api import rest_api
from phlo.ingestion import phlo_ingestion

from workflows.schemas.github import RawUserProfile


@phlo_ingestion(
    table_name="user_profile",
    unique_key="id",
    validation_schema=RawUserProfile,
    group="github",
    cron="0 */6 * * *",
    freshness_hours=(6, 24),
    merge_strategy="merge",
    merge_config={"deduplication_method": "last"},
)
def user_profile(partition_date: str):
    """Ingest GitHub user profile data.

    Uses merge strategy because profile data changes over time:
    - User bio, location, company can be updated
    - Follower counts change
    - Profile picture URLs may change

    The "last" dedup strategy keeps the most recent profile snapshot.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_username = os.getenv("GITHUB_USERNAME", "iamgp")

    return rest_api(
        client={
            "base_url": "https://api.github.com",
            "headers": {
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        },
        resources=[
            {
                "name": "profile",
                "endpoint": {
                    "path": f"users/{github_username}",
                },
            }
        ],
    )
