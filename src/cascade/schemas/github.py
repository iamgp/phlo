# github.py - Pandera schemas for validating GitHub user events and repository statistics
# Defines data quality checks and type validation for processed GitHub data
# Used by Dagster asset checks to ensure data integrity across transformations

from __future__ import annotations

from datetime import datetime

from dagster_pandera import pandera_schema_to_dagster_type
from pandera.pandas import DataFrameModel, Field

# --- Validation Constants ---
# Constants used for GitHub data validation rules
VALID_EVENT_TYPES = [
    "CommitCommentEvent",
    "CreateEvent",
    "DeleteEvent",
    "ForkEvent",
    "GollumEvent",
    "IssueCommentEvent",
    "IssuesEvent",
    "MemberEvent",
    "PublicEvent",
    "PullRequestEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "PushEvent",
    "ReleaseEvent",
    "SponsorshipEvent",
    "WatchEvent",
]


# --- Pandera Schemas ---
# DataFrame schemas for validating structured data in the pipeline
class GitHubUserEvents(DataFrameModel):
    """
    Schema for the user_events table.

    Validates processed GitHub user events including:
    - Valid event types and IDs
    - Proper timestamp formatting
    - Required actor and repo information
    - Public/private event flags
    """

    id: str = Field(
        nullable=False,
        unique=True,
        description="Unique identifier for the GitHub event",
    )

    type: str = Field(
        isin=VALID_EVENT_TYPES,
        nullable=False,
        description="Type of GitHub event (e.g., 'PushEvent', 'IssuesEvent')",
    )

    actor: str = Field(
        nullable=False,
        description="JSON string containing actor information",
    )

    repo: str = Field(
        nullable=False,
        description="JSON string containing repository information",
    )

    payload: str = Field(
        nullable=False,
        description="JSON string containing event payload data",
    )

    public: bool = Field(
        nullable=False,
        description="Whether the event is public or private",
    )

    created_at: datetime = Field(
        nullable=False,
        description="Timestamp when the event was created",
    )

    org: str | None = Field(
        nullable=True,
        description="JSON string containing organization information (nullable)",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True  # Auto type coercion where possible


class GitHubRepoStats(DataFrameModel):
    """
    Schema for the repo_stats table.

    Validates processed GitHub repository statistics including:
    - Repository identification fields
    - Collection date validation
    - JSON structure for statistics data
    """

    repo_name: str = Field(
        nullable=False,
        description="Name of the repository",
    )

    repo_full_name: str = Field(
        nullable=False,
        description="Full name of the repository (owner/repo)",
    )

    repo_id: int = Field(
        nullable=False,
        description="GitHub repository ID",
    )

    collection_date: str = Field(
        nullable=False,
        description="Date when statistics were collected (YYYY-MM-DD)",
    )

    contributors_data: str | None = Field(
        nullable=True,
        description="JSON string containing contributors statistics",
    )

    commit_activity_data: str | None = Field(
        nullable=True,
        description="JSON string containing commit activity statistics",
    )

    code_frequency_data: str | None = Field(
        nullable=True,
        description="JSON string containing code frequency statistics",
    )

    participation_data: str | None = Field(
        nullable=True,
        description="JSON string containing participation statistics",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True  # Auto type coercion where possible


# --- Dagster Type Conversion ---
# Caching and conversion utilities for Dagster integration
# Lazy-load Dagster types to avoid import-time overhead
_dagster_user_events_type_cache = None
_dagster_repo_stats_type_cache = None


# --- Helper Functions ---
# Utility functions for schema integration
def get_github_user_events_dagster_type():
    """Get or create the Dagster type from GitHub user events Pandera schema."""
    global _dagster_user_events_type_cache
    if _dagster_user_events_type_cache is None:
        _dagster_user_events_type_cache = pandera_schema_to_dagster_type(GitHubUserEvents)
    return _dagster_user_events_type_cache


def get_github_repo_stats_dagster_type():
    """Get or create the Dagster type from GitHub repo stats Pandera schema."""
    global _dagster_repo_stats_type_cache
    if _dagster_repo_stats_type_cache is None:
        _dagster_repo_stats_type_cache = pandera_schema_to_dagster_type(GitHubRepoStats)
    return _dagster_repo_stats_type_cache
