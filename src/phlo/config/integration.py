from pathlib import Path

from pydantic import Field, computed_field

from phlo.config.base import BaseConfig


class IntegrationConfig(BaseConfig):
    """External service integrations (OpenMetadata, dbt, Superset)."""

    superset_port: int = Field(default=10007, description="Superset web port")
    superset_admin_user: str = Field(default="admin", description="Superset admin username")
    superset_admin_password: str = Field(default="admin", description="Superset admin password")
    superset_admin_email: str = Field(
        default="admin@example.com", description="Superset admin email"
    )

    workflows_path: str = Field(
        default="workflows",
        description="Path to user workflows directory (for external projects)",
    )
    dbt_project_dir: str = Field(
        default="workflows/transforms/dbt",
        description="Path to dbt project directory",
    )
    dbt_manifest_path: str = Field(
        default="",
        description="Path to dbt manifest.json after running dbt docs generate",
    )
    dbt_catalog_path: str = Field(
        default="",
        description="Path to dbt catalog.json for column-level documentation",
    )

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

    @computed_field
    @property
    def dbt_profiles_dir(self) -> str:
        """dbt profiles directory - derived from dbt_project_dir."""
        return f"{self.dbt_project_dir}/profiles"

    @property
    def openmetadata_uri(self) -> str:
        """Return OpenMetadata API base URI."""
        return f"http://{self.openmetadata_host}:{self.openmetadata_port}/api"

    @property
    def dbt_project_path(self) -> Path:
        """Return dbt project directory as Path object."""
        return Path(self.dbt_project_dir)

    @property
    def dbt_profiles_path(self) -> Path:
        """Return dbt profiles directory as Path object."""
        return Path(self.dbt_profiles_dir)
