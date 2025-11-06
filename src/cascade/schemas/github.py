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

class RawGitHubUserEvents(DataFrameModel):
    """
    Schema for raw GitHub user events from the API.

    Validates raw GitHub user events at ingestion time before dbt transformation:
    - Valid event types
    - Required fields (id, type, actor, repo, payload)
    - Proper timestamp formatting
    - Unique event IDs
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

    _cascade_ingested_at: datetime = Field(
        nullable=False,
        description="Timestamp when data was ingested by Cascade",
    )

    class Config:
        strict = False  # Allow DLT metadata fields
        coerce = True


class RawGitHubRepoStats(DataFrameModel):
    """
    Schema for raw GitHub repository statistics from the API.

    Validates raw repository statistics at ingestion time before dbt transformation:
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

    _cascade_ingested_at: datetime = Field(
        nullable=False,
        description="Timestamp when data was ingested by Cascade",
    )

    class Config:
        strict = False  # Allow DLT metadata fields
        coerce = True


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


class FactGitHubUserEvents(DataFrameModel):
    """
    Schema for the fct_github_user_events fact table (silver layer).

    Validates enriched GitHub user events with calculated metrics:
    - Event categorization
    - Extracted JSON fields (actor_login, repo_name, etc.)
    - Time dimensions (hour_of_day, day_of_week)
    - Boolean flags (is_repo_public, involves_organization)
    """

    event_id: str = Field(
        nullable=False,
        unique=True,
        description="Unique identifier for the GitHub event",
    )

    event_type: str = Field(
        isin=VALID_EVENT_TYPES,
        nullable=False,
        description="Type of GitHub event",
    )

    event_category: str = Field(
        isin=[
            "code_contribution",
            "issue_management",
            "pull_request",
            "repository_management",
            "social",
            "collaboration",
            "release_management",
            "documentation",
            "visibility",
            "other",
        ],
        nullable=False,
        description="Categorized event type for analytics",
    )

    actor_login: str = Field(
        nullable=False,
        description="GitHub username of the actor (extracted from JSON)",
    )

    actor_id: str = Field(
        nullable=False,
        description="GitHub actor ID (extracted from JSON)",
    )

    repo_name: str = Field(
        nullable=False,
        description="Repository name (extracted from JSON)",
    )

    repo_full_name: str = Field(
        nullable=False,
        description="Full repository name owner/repo (extracted from JSON)",
    )

    public: bool = Field(
        nullable=False,
        description="Whether the event is public",
    )

    is_repo_public: bool = Field(
        nullable=False,
        description="Whether the repository is public",
    )

    involves_organization: bool = Field(
        nullable=False,
        description="Whether the event involves an organization",
    )

    created_at: datetime = Field(
        nullable=False,
        description="Event creation timestamp",
    )

    event_date: datetime = Field(
        nullable=False,
        description="Date of the event (truncated to day)",
    )

    hour_of_day: int = Field(
        ge=0,
        le=23,
        nullable=False,
        description="Hour when event occurred (0-23)",
    )

    day_of_week: int = Field(
        ge=1,
        le=7,
        nullable=False,
        description="Day of week (1=Monday, 7=Sunday)",
    )

    day_name: str = Field(
        nullable=False,
        description="Name of the day (e.g., 'Monday', 'Tuesday')",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True


class FactGitHubRepoStats(DataFrameModel):
    """
    Schema for the fct_github_repo_stats fact table (silver layer).

    Validates enriched GitHub repository statistics with calculated metrics:
    - Contributor counts
    - Commit activity summaries
    - Activity scores
    - Classification fields (contribution_level, activity_level, repository_health)
    """

    repo_name: str = Field(
        nullable=False,
        description="Name of the repository",
    )

    repo_full_name: str = Field(
        nullable=False,
        unique=True,
        description="Full name of the repository (owner/repo)",
    )

    repo_id: int = Field(
        nullable=False,
        unique=True,
        description="GitHub repository ID",
    )

    repo_owner: str = Field(
        nullable=False,
        description="Repository owner (extracted from full_name)",
    )

    repo_short_name: str = Field(
        nullable=False,
        description="Repository short name (extracted from full_name)",
    )

    collection_date: str = Field(
        nullable=False,
        description="Date when statistics were collected (YYYY-MM-DD)",
    )

    contributor_count: int = Field(
        ge=0,
        nullable=False,
        description="Number of contributors",
    )

    total_commits_last_52_weeks: int = Field(
        ge=0,
        nullable=False,
        description="Total commits in last 52 weeks",
    )

    weeks_with_activity: int = Field(
        ge=0,
        nullable=False,
        description="Number of weeks with activity",
    )

    activity_score: int | float = Field(
        ge=0,
        nullable=False,
        description="Calculated activity score",
    )

    contribution_level: str = Field(
        isin=["high_contribution", "medium_contribution", "low_contribution", "no_contribution"],
        nullable=False,
        description="Contribution level classification",
    )

    activity_level: str = Field(
        isin=["very_active", "active", "moderate", "inactive"],
        nullable=False,
        description="Activity level classification",
    )

    repository_health: str = Field(
        isin=["healthy", "stable", "developing", "dormant"],
        nullable=False,
        description="Repository health status",
    )

    avg_commits_per_week: float | None = Field(
        ge=0,
        nullable=True,
        description="Average commits per week",
    )

    class Config:
        strict = True  # No additional columns allowed
        coerce = True


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
