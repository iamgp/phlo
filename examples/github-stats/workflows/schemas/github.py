"""
Pandera schemas for github domain.

Schemas define data validation rules and auto-generate Iceberg schemas.

Note: For optional fields (str | None), always use Field(nullable=True).
This is required because Pandera's coerce=True needs explicit nullable flag.
"""

from pandera.pandas import Field
from phlo_quality.schemas import PhloSchema


class RawUserEvents(PhloSchema):
    """Raw user events data schema."""

    id: int = Field(unique=True)  # GitHub event IDs are integers
    type: str | None = Field(nullable=True)
    created_at: str | None = Field(nullable=True)
    actor__login: str | None = Field(nullable=True)
    repo__name: str | None = Field(nullable=True)


class RawUserRepos(PhloSchema):
    """Raw user repositories data schema."""

    id: int = Field(unique=True)
    name: str
    full_name: str
    stargazers_count: int = Field(ge=0)
    forks_count: int = Field(ge=0)
    language: str | None = Field(nullable=True)
    created_at: str
    updated_at: str


class RawUserProfile(PhloSchema):
    """Raw user profile data schema."""

    id: int = Field(unique=True)
    login: str
    name: str | None = Field(nullable=True)
    followers: int = Field(ge=0)
    following: int = Field(ge=0)
    public_repos: int = Field(ge=0)
    created_at: str
