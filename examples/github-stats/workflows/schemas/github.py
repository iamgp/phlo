"""
Pandera schemas for github domain.

Schemas define data validation rules and auto-generate Iceberg schemas.
"""

from pandera.pandas import DataFrameModel, Field


class RawUserEvents(DataFrameModel):
    """Raw user events data schema."""

    id: str = Field(
        description="Unique identifier for deduplication",
        nullable=False,
    )
    type: str = Field(description="Event type", nullable=False)
    created_at: str = Field(description="Event timestamp", nullable=False)
    actor__login: str | None = Field(description="Actor username", nullable=True)
    repo__name: str | None = Field(description="Repository name", nullable=True)

    class Config:
        strict = False
        coerce = True


class RawUserRepos(DataFrameModel):
    """Raw user repositories data schema."""

    id: int = Field(
        description="Unique repository identifier",
        nullable=False,
    )
    name: str = Field(description="Repository name", nullable=False)
    full_name: str = Field(description="Full repository name (owner/repo)", nullable=False)
    stargazers_count: int = Field(ge=0, description="Number of stars", nullable=False)
    forks_count: int = Field(ge=0, description="Number of forks", nullable=False)
    language: str | None = Field(description="Primary language", nullable=True)
    created_at: str = Field(description="Repository creation timestamp", nullable=False)
    updated_at: str = Field(description="Last update timestamp", nullable=False)

    class Config:
        strict = False
        coerce = True


class RawUserProfile(DataFrameModel):
    """Raw user profile data schema."""

    id: int = Field(
        description="Unique user identifier",
        nullable=False,
    )
    login: str = Field(description="Username", nullable=False)
    name: str | None = Field(description="Display name", nullable=True)
    followers: int = Field(ge=0, description="Number of followers", nullable=False)
    following: int = Field(ge=0, description="Number following", nullable=False)
    public_repos: int = Field(ge=0, description="Number of public repos", nullable=False)
    created_at: str = Field(description="Account creation timestamp", nullable=False)

    class Config:
        strict = False
        coerce = True
