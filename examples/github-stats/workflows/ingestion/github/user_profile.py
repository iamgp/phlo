"""Github user_profile ingestion asset."""

from __future__ import annotations

from phlo_dlt import phlo_ingestion

from workflows.ingestion.github.helpers import github_api
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
    return github_api(
        resource="profile",
        path="users/{username}",
    )
