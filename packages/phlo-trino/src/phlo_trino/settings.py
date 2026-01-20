"""Trino settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


def build_trino_dsn(host: str, port: int, catalog: str) -> str:
    return f"trino://{host}:{port}/{catalog}"


class TrinoSettings(BaseConfig):
    """Trino query engine configuration."""

    trino_version: str = Field(default="477", description="Trino version")
    trino_port: int = Field(default=10005, description="Trino HTTP port")
    trino_host: str = Field(default="trino", description="Trino service hostname")
    trino_catalog: str = Field(default="iceberg", description="Trino catalog name for Iceberg")

    def trino_connection_string(self) -> str:
        return build_trino_dsn(self.trino_host, self.trino_port, self.trino_catalog)


@lru_cache(maxsize=1)
def get_settings() -> TrinoSettings:
    return TrinoSettings()
