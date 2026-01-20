"""OpenMetadata settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo_trino.settings import get_settings as get_trino_settings


class OpenMetadataSettings(BaseConfig):
    """OpenMetadata integration configuration."""

    openmetadata_host: str = Field(
        default="openmetadata-server", description="OpenMetadata server hostname"
    )
    openmetadata_port: int = Field(default=8585, description="OpenMetadata server port")
    openmetadata_username: str = Field(default="admin", description="OpenMetadata admin username")
    openmetadata_password: str = Field(default="admin", description="OpenMetadata admin password")
    openmetadata_verify_ssl: bool = Field(
        default=False, description="Verify SSL certificates for OpenMetadata connections"
    )
    openmetadata_service_name: str = Field(
        default="phlo",
        description="OpenMetadata database service name for Phlo metadata sync",
    )
    openmetadata_service_type: str = Field(
        default="Trino",
        description="OpenMetadata database service type (e.g., Trino, Postgres)",
    )
    openmetadata_database_name: str | None = Field(
        default=None,
        description="OpenMetadata database name (defaults to Trino catalog if unset)",
    )
    openmetadata_sync_enabled: bool = Field(
        default=True, description="Enable automatic metadata sync to OpenMetadata"
    )
    openmetadata_sync_interval_seconds: int = Field(
        default=300, description="Minimum interval between metadata syncs (seconds)"
    )

    def openmetadata_uri(self) -> str:
        return f"http://{self.openmetadata_host}:{self.openmetadata_port}/api"

    def openmetadata_database(self) -> str:
        if self.openmetadata_database_name:
            return self.openmetadata_database_name
        return get_trino_settings().trino_catalog


@lru_cache(maxsize=1)
def get_settings() -> OpenMetadataSettings:
    return OpenMetadataSettings()
