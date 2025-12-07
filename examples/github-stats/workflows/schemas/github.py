"""
Pandera schemas for github domain.

Schemas define data validation rules and auto-generate Iceberg schemas.
"""

from pandera.pandas import Field

from phlo.schemas import PhloSchema


class RawUserEvents(PhloSchema):
    """Raw user events data schema."""

    id: str = Field(unique=True)
    type: str
    created_at: str
    actor__login: str | None
    repo__name: str | None


class RawUserRepos(PhloSchema):
    """Raw user repositories data schema."""

    id: int = Field(unique=True)
    name: str
    full_name: str
    stargazers_count: int = Field(ge=0)
    forks_count: int = Field(ge=0)
    language: str | None
    created_at: str
    updated_at: str


class RawUserProfile(PhloSchema):
    """Raw user profile data schema."""

    id: int = Field(unique=True)
    login: str
    name: str | None
    followers: int = Field(ge=0)
    following: int = Field(ge=0)
    public_repos: int = Field(ge=0)
    created_at: str
