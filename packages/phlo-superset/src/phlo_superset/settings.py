"""Superset settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class SupersetSettings(BaseConfig):
    """Superset configuration."""

    superset_port: int = Field(default=10007, description="Superset web port")
    superset_admin_user: str = Field(default="admin", description="Superset admin username")
    superset_admin_password: str = Field(default="admin", description="Superset admin password")
    superset_admin_email: str = Field(
        default="admin@example.com", description="Superset admin email"
    )


@lru_cache(maxsize=1)
def get_settings() -> SupersetSettings:
    """Get cached Superset settings.

    Returns:
        Loaded Superset configuration settings.
    """
    return SupersetSettings()
