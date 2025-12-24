"""Github user_repos ingestion asset."""

from __future__ import annotations

from phlo_dlt import phlo_ingestion

from workflows.ingestion.github.helpers import github_api
from workflows.schemas.github import RawUserRepos


@phlo_ingestion(
    table_name="user_repos",
    unique_key="id",
    validation_schema=RawUserRepos,
    group="github",
    cron="0 */6 * * *",
    freshness_hours=(6, 24),
    merge_strategy="merge",
    merge_config={"deduplication_method": "last"},
)
def user_repos(partition_date: str):
    """Ingest GitHub repository metadata.

    Uses merge strategy because repository metadata changes:
    - Descriptions, topics, and README content can be updated
    - Star counts and fork counts increase
    - Language statistics change as code is added
    - Repository settings (private/public, archived) can change

    The "last" dedup strategy keeps the most recent repository snapshot.
    """
    return github_api(
        resource="repos",
        # Use the authenticated endpoint so we get all accessible repos (owner, org, collaborator),
        # not just the public repos for a username.
        path="user/repos",
        params={
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
            "visibility": "all",
            "affiliation": "owner,collaborator,organization_member",
        },
    )
