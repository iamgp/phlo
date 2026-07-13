"""Lineage settings and configuration management.

This module provides Pydantic-based configuration management for the phlo-lineage
package. It defines the LineageSettings class which handles environment variable
resolution for database connection strings and other lineage-related configuration.

Configuration Sources:
    Settings are loaded from environment variables using Pydantic's
    validation_alias feature, which supports multiple fallback variable names.

Priority Order for lineage_db_url:
    1. LINEAGE_DB_URL
    2. PHLO_LINEAGE_DB_URL
    3. DAGSTER_PG_DB_CONNECTION_STRING

Usage:
    Settings are accessed via the cached get_settings() function, which returns
    a project-root-scoped instance parsed from the environment.

Example:
    >>> from phlo_lineage.settings import get_settings, LineageSettings
    >>>
    >>> # Access cached settings
    >>> settings = get_settings()
    >>> print(settings.lineage_db_url)
    'postgresql://user:pass@localhost:5432/phlo'
    >>>
    >>> # Create settings directly (bypass cache)
    >>> settings = LineageSettings()  # Reads env vars fresh

Environment Variables:
    LINEAGE_DB_URL: Primary lineage database URL.
    PHLO_LINEAGE_DB_URL: Fallback lineage database URL.
    DAGSTER_PG_DB_CONNECTION_STRING: Dagster database URL (tertiary fallback).

See Also:
    phlo.config.base.BaseConfig for the base configuration class.

"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached


class LineageSettings(BaseConfig):
    """Configuration settings for the lineage store and related features.

    This Pydantic model defines all configuration options for phlo-lineage,
    with automatic environment variable loading and validation.

    Attributes:
        lineage_db_url: PostgreSQL connection string for the lineage database.
            Supports multiple environment variable aliases for flexibility
            across different deployment scenarios.

    Configuration Precedence:
        lineage_db_url is resolved from the first available source:
        1. LINEAGE_DB_URL (explicit lineage setting)
        2. PHLO_LINEAGE_DB_URL (namespaced lineage setting)
        3. DAGSTER_PG_DB_CONNECTION_STRING (reuse Dagster's database)

    Inheritance:
        Inherits from BaseConfig which provides common Pydantic settings
        like extra="forbid" and environment variable parsing.

    Example:
        >>> import os
        >>> os.environ["LINEAGE_DB_URL"] = "postgresql://localhost/lineage"
        >>>
        >>> settings = LineageSettings()
        >>> print(settings.lineage_db_url)
        'postgresql://localhost/lineage'

    See Also:
        https://docs.pydantic.dev/latest/concepts/fields/#aliaschoices
        for multiple alias handling.

    """

    lineage_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LINEAGE_DB_URL",
            "PHLO_LINEAGE_DB_URL",
            "DAGSTER_PG_DB_CONNECTION_STRING",
        ),
        description="PostgreSQL DSN for the row-level lineage store",
    )


@project_root_cached
def get_settings(project_root: Path) -> LineageSettings:
    """Get cached LineageSettings for the selected project root.

    Settings are cached after first access per resolved project root, with
    up to 16 entries, avoiding repeated environment variable parsing while
    keeping project configuration isolated.

    Args:
        project_root: Resolved project root used for cache selection.

    Returns:
        LineageSettings instance loaded from environment variables.

    Caching:
        Settings are cached with up to 16 resolved project roots. The cache
        is process-local and thread-safe.

        To reload settings (e.g., after environment changes):
        >>> get_settings.cache_clear()
        >>> new_settings = get_settings()

    Example:
        >>> from phlo_lineage.settings import get_settings
        >>>
        >>> settings = get_settings()
        >>> if settings.lineage_db_url:
        ...     print("Lineage database configured")
        ... else:
        ...     print("No lineage database URL found")

    Thread Safety:
        The project-root cache provides thread-safe caching. The
        LineageSettings instance itself is immutable after creation.

    Performance:
        First call: Parses environment variables (~0.1-1ms)
        Subsequent calls for the same root: Returns cached instance (O(1))

    See Also:
        phlo.config.cache.project_root_cached for caching behavior details.

    """
    return LineageSettings()
