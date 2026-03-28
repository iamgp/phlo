"""Settings for phlo-sling package.

This module defines the configuration settings for the phlo-sling package,
including defaults for replication modes, namespace handling, and connection
management. Settings are loaded from environment variables and configuration
files with sensible defaults.

Classes:
    SlingSettings: Pydantic-based configuration class for Sling settings.

Functions:
    get_settings: Returns a cached instance of SlingSettings.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class SlingSettings(BaseConfig):
    """Configuration for Sling replication defaults.

    This class defines the configuration schema and defaults for Sling
    replication operations within the Phlo platform. Settings are loaded
    from environment variables prefixed appropriately and validated
    using Pydantic.

    Attributes:
        sling_default_namespace: Default namespace/prefix for generated
            replication table names. Tables will be created as
            ``{namespace}.{table_name}``.
        sling_binary_path: Override path to the Sling binary executable.
            If None, the bundled binary from the sling package is used.
        sling_default_mode: Default replication mode for Sling operations.
            Valid modes are "full-refresh", "incremental", "snapshot",
            and "backfill".
        sling_auto_connections: Whether to automatically generate Sling
            connection definitions from Phlo capability metadata.
        sling_connections_dir: Directory path containing Sling env.yaml
            files for explicit connection definitions. If provided,
            these connections are merged with auto-discovered ones.

    Example:
        Load settings with defaults::

            from phlo_sling.settings import get_settings

            settings = get_settings()
            print(settings.sling_default_namespace)  # "raw"

    """

    sling_default_namespace: str = Field(
        default="raw",
        description="Default namespace for generated replication table names.",
    )
    sling_binary_path: str | None = Field(
        default=None,
        description="Override path to the sling binary. None uses the bundled binary.",
    )
    sling_default_mode: str = Field(
        default="incremental",
        description="Default replication mode (full-refresh, incremental, snapshot, backfill).",
    )
    sling_auto_connections: bool = Field(
        default=True,
        description="Auto-generate Sling connections from Phlo capability metadata.",
    )
    sling_connections_dir: str | None = Field(
        default=None,
        description="Directory containing Sling env.yaml files for explicit connections.",
    )


@lru_cache(maxsize=1)
def get_settings() -> SlingSettings:
    """Return cached Sling settings instance.

    Returns a singleton instance of SlingSettings using LRU caching to
    avoid repeated configuration loading. The settings are loaded from
    environment variables and configuration files on first access.

    Returns:
        Cached SlingSettings instance with loaded configuration values.

    Example:
        Get settings in application code::

            settings = get_settings()
            namespace = settings.sling_default_namespace

    """
    return SlingSettings()
