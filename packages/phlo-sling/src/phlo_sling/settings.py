"""Settings for phlo-sling package."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class SlingSettings(BaseConfig):
    """Configuration for Sling replication defaults."""

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
    """Return cached Sling settings instance."""
    return SlingSettings()
