"""Nessie settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class NessieSettings(BaseConfig):
    """Nessie catalog configuration."""

    nessie_version: str = Field(default="0.106.0", description="Nessie version")
    nessie_port: int = Field(default=19120, description="Nessie REST API port")
    nessie_host: str = Field(default="nessie", description="Nessie service hostname")
    nessie_api_version: str = Field(default="v1", description="Nessie API version")
    nessie_default_ref: str = Field(
        default="main",
        description="Default Nessie branch/tag",
    )

    def nessie_uri(self) -> str:
        """Return the base Nessie API URI.

        Returns:
            str: Base URI for Nessie API endpoints.
        """
        return f"http://{self.nessie_host}:{self.nessie_port}/api"

    def nessie_api_uri(self) -> str:
        """Return the versioned Nessie API URI.

        Returns:
            str: Versioned URI for Nessie API endpoints.
        """
        return f"http://{self.nessie_host}:{self.nessie_port}/api/{self.nessie_api_version}"

    def nessie_iceberg_rest_uri(self) -> str:
        """Return the Nessie Iceberg REST catalog URI.

        Returns:
            str: URI for Iceberg REST catalog integration.
        """
        return f"http://{self.nessie_host}:{self.nessie_port}/iceberg"


@lru_cache(maxsize=1)
def get_settings() -> NessieSettings:
    """Return cached Nessie settings.

    Returns:
        NessieSettings: Singleton settings instance.
    """
    return NessieSettings()
