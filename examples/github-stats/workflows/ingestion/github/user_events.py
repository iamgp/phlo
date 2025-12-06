"""Github user_events ingestion asset."""

from __future__ import annotations

import os

from dlt.sources.rest_api import rest_api
from phlo.ingestion import phlo_ingestion

from workflows.schemas.github import RawUserEvents


@phlo_ingestion(
    table_name="user_events",
    unique_key="id",
    validation_schema=RawUserEvents,
    group="github",
    cron="0 */6 * * *",
    freshness_hours=(6, 24),
    merge_strategy="append",
    merge_config={"deduplication": True, "deduplication_method": "hash"},
)
def user_events(partition_date: str):
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
                "name": "events",
                "endpoint": {
                    "path": f"users/{github_username}/events",
                    "params": {
                        "per_page": 100,
                    },
                },
            }
        ],
    )
