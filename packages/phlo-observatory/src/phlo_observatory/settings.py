"""Observatory UI settings and configuration.

This module provides the settings infrastructure for the Observatory UI package,
including database connection configuration for persistent settings storage.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class ObservatorySettings(BaseConfig):
    """Configuration settings for the Observatory UI.

    Attributes:
        observatory_settings_db_url: PostgreSQL connection string for persisting
            Observatory settings. If not provided, settings are stored in-memory.

    Example:
        >>> settings = get_settings()
        >>> print(settings.observatory_settings_db_url)
        'postgresql://user:pass@localhost/observatory'

    """

    observatory_settings_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_OBSERVATORY_SETTINGS_DB_URL"),
        description="PostgreSQL DSN for Observatory settings storage",
    )


@lru_cache(maxsize=1)
def get_settings() -> ObservatorySettings:
    """Return cached Observatory settings instance.

    Settings are parsed from environment variables using PHLO_OBSERVATORY_*
    prefixes and cached for the lifetime of the process.

    Returns:
        ObservatorySettings: Parsed and validated Observatory settings.

    Example:
        >>> settings = get_settings()
        >>> db_url = settings.observatory_settings_db_url

    """

    return ObservatorySettings()
