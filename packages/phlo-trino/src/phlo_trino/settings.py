"""Trino settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


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
        validation_alias=AliasChoices(
            "TRINO_DEFAULT_REF",
            "PHLO_TRINO_DEFAULT_REF",
            "PHLO_DEFAULT_REF",
            "ICEBERG_NESSIE_REF",
            "PHLO_ICEBERG_NESSIE_REF",
        ),
        description="Default branch/tag suffix",
    )

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
