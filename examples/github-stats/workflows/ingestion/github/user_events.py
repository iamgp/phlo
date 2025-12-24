"""Github user_events ingestion asset."""

from __future__ import annotations

from phlo_dlt import phlo_ingestion

from workflows.ingestion.github.helpers import github_api
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
    return github_api(
        resource="events",
        path="users/{username}/events",
        params={"per_page": 100},
    )
