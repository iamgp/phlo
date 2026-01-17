"""Observatory settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class ObservatorySettings(BaseConfig):
    """Observatory configuration."""

    observatory_settings_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_OBSERVATORY_SETTINGS_DB_URL"),
        description="PostgreSQL DSN for Observatory settings storage",
    )


@lru_cache(maxsize=1)
def get_settings() -> ObservatorySettings:
    return ObservatorySettings()
