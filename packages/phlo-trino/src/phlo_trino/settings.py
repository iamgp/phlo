"""Trino settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.network import resolve_host


def build_trino_dsn(host: str, port: int, catalog: str) -> str:
    """Build a Trino DSN string.

    Args:
        host: Trino hostname.
        port: Trino HTTP port.
        catalog: Trino catalog name.

    Returns:
        DSN string for Trino connections.
    """
    return f"trino://{host}:{port}/{catalog}"


class TrinoSettings(BaseConfig):
    """Trino query engine configuration."""

    trino_version: str = Field(default="477", description="Trino version")
    trino_port: int = Field(default=10005, description="Trino HTTP port")
    trino_host: str = Field(default="trino", description="Trino service hostname")
    trino_catalog: str = Field(default="iceberg", description="Trino catalog name for Iceberg")
    trino_default_ref: str = Field(
        default="main",
        description="Default branch/tag suffix",
    )

    def model_post_init(self, __context: Any) -> None:
        host, port = resolve_host(self.trino_host, self.trino_port, port_env_var="TRINO_PORT")
        object.__setattr__(self, "trino_host", host)
        object.__setattr__(self, "trino_port", port)

    def trino_connection_string(self) -> str:
        """Return the Trino DSN for current settings.

        Returns:
            DSN string derived from configured host, port, and catalog.
        """
        return build_trino_dsn(self.trino_host, self.trino_port, self.trino_catalog)


@lru_cache(maxsize=1)
def get_settings() -> TrinoSettings:
    """Return cached Trino settings.

    Returns:
        Trino settings instance.
    """
    return TrinoSettings()
