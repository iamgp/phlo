"""OpenMetadata settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo_openmetadata.capabilities import resolve_query_engine_catalog


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
    openmetadata_catalog_scanner: str | None = Field(
        default=None,
        description="Catalog scanner capability name to use for sync operations",
    )
    openmetadata_query_engine: str | None = Field(
        default=None,
        description="Query engine capability name used to infer the OpenMetadata database name",
    )
    openmetadata_default_catalog: str = Field(
        default="iceberg",
        description="Fallback catalog/database name when query-engine metadata is unavailable",
    )
    openmetadata_database_name: str | None = Field(
        default=None,
        description="OpenMetadata database name (defaults to Trino catalog if unset)",
    )
    openmetadata_dbt_manifest_path: str = Field(
        default="workflows/transforms/dbt/target/manifest.json",
        description="Path to dbt manifest.json for metadata sync",
    )
    openmetadata_dbt_catalog_path: str = Field(
        default="workflows/transforms/dbt/target/catalog.json",
        description="Path to dbt catalog.json for metadata sync",
    )
    openmetadata_sync_enabled: bool = Field(
        default=True, description="Enable automatic metadata sync to OpenMetadata"
    )
    openmetadata_sync_interval_seconds: int = Field(
        default=300, description="Minimum interval between metadata syncs (seconds)"
    )

    def openmetadata_uri(self) -> str:
        """Build the OpenMetadata API base URI.

        Returns:
            str: Base API URI for OpenMetadata.
        """
        return f"http://{self.openmetadata_host}:{self.openmetadata_port}/api"

    def openmetadata_database(self) -> str:
        """Resolve the OpenMetadata database name.

        Returns:
            str: Explicit OpenMetadata database name or Trino catalog fallback.
        """
        if self.openmetadata_database_name:
            return self.openmetadata_database_name
        return resolve_query_engine_catalog(
            self.openmetadata_query_engine,
            default=self.openmetadata_default_catalog,
        )


@lru_cache(maxsize=1)
def get_settings() -> OpenMetadataSettings:
    """Get cached OpenMetadata settings.

    Returns:
        OpenMetadataSettings: Cached OpenMetadata settings instance.
    """
    return OpenMetadataSettings()
