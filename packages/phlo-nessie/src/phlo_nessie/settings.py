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

    def nessie_uri(self) -> str:
        return f"http://{self.nessie_host}:{self.nessie_port}/api"

    def nessie_api_uri(self) -> str:
        return f"http://{self.nessie_host}:{self.nessie_port}/api/{self.nessie_api_version}"

    def nessie_iceberg_rest_uri(self) -> str:
        return f"http://{self.nessie_host}:{self.nessie_port}/iceberg"


@lru_cache(maxsize=1)
def get_settings() -> NessieSettings:
    return NessieSettings()
