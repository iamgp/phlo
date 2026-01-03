# config.py - Centralized configuration management for the Phlo lakehouse platform
# This module defines all configurable settings using Pydantic, loaded from environment variables
# and .phlo/.env(.local) files. It provides computed properties for connection strings and catalog configs.

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Settings class: Main configuration class extending Pydantic BaseSettings
# Loads from .phlo/.env(.local) and environment variables, provides validation and type safety
class Settings(BaseSettings):
    """Centralized configuration for phlo using environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".phlo/.env", ".phlo/.env.local"),
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database Configuration ---
    # Settings for PostgreSQL database connection and schema configuration
    # Database - Postgres
    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=10000, description="PostgreSQL port")
    postgres_user: str = Field(default="lake", description="PostgreSQL username")
    postgres_password: str = Field(default="phlo", description="PostgreSQL password")
    postgres_db: str = Field(default="lakehouse", description="PostgreSQL database name")
    postgres_mart_schema: str = Field(
        default="marts", description="Schema for published mart tables"
    )
    lineage_db_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_LINEAGE_DB_URL", "DAGSTER_PG_DB_CONNECTION_STRING"),
        description="PostgreSQL DSN for the row-level lineage store",
    )

    # --- Storage Configuration ---
    # Settings for MinIO S3-compatible object storage
    # Storage - MinIO
    minio_host: str = Field(default="minio", description="MinIO service hostname")
    minio_root_user: str = Field(default="minio", description="MinIO root username")
    minio_root_password: str = Field(default="minio123", description="MinIO root password")
    minio_api_port: int = Field(default=10001, description="MinIO API port")
    minio_console_port: int = Field(default=10002, description="MinIO console port")

    # --- Catalog Configuration ---
    # Settings for Nessie Git-like catalog for Iceberg table management
    # Catalog - Nessie
    nessie_version: str = Field(default="0.106.0", description="Nessie version")
    nessie_port: int = Field(default=19120, description="Nessie REST API port")
    nessie_host: str = Field(default="nessie", description="Nessie service hostname")

    # --- Query Engine Configuration ---
    # Settings for Trino distributed SQL query engine
    # Query Engine - Trino
    trino_version: str = Field(default="477", description="Trino version")
    trino_port: int = Field(default=10005, description="Trino HTTP port")
    trino_host: str = Field(default="trino", description="Trino service hostname")
    trino_catalog: str = Field(default="iceberg", description="Trino catalog name for Iceberg")

    # --- Data Lake Configuration ---
    # Settings for Iceberg table format and warehouse paths
    # Data Lake - Iceberg
    iceberg_warehouse_path: str = Field(
        default="s3://lake/warehouse", description="S3 path for Iceberg warehouse"
    )
    iceberg_staging_path: str = Field(
        default="s3://lake/stage", description="S3 path for staging parquet files"
    )
    iceberg_default_namespace: str = Field(
        default="raw", description="Default namespace/schema for Iceberg tables"
    )
    iceberg_nessie_ref: str = Field(
        default="main", description="Default Nessie branch/tag for Iceberg operations"
    )

    # --- Nessie Branch Management ---
    # Settings for dynamic branch workflow and validation gates
    branch_retention_days: int = Field(
        default=7, description="Days to retain pipeline branches after successful merge"
    )
    branch_retention_days_failed: int = Field(
        default=14,
        description="Days to retain pipeline branches that failed validation",
    )
    auto_promote_enabled: bool = Field(
        default=True,
        description="Enable automatic promotion to main after validation passes",
    )
    branch_cleanup_enabled: bool = Field(
        default=False,
        description="Enable automatic branch cleanup (set True in production)",
    )

    # --- Validation Gates Configuration ---
    # Settings for data quality validation and promotion gates
    freshness_blocks_promotion: bool = Field(
        default=False,
        description="Whether freshness policy failures should block promotion to main",
    )
    pandera_critical_level: str = Field(
        default="error",
        description="Pandera check severity that blocks promotion (error|warning|info)",
    )

    # --- Validation Retry Configuration ---
    # Settings for automatic retry of failed validations
    validation_retry_enabled: bool = Field(
        default=True, description="Enable automatic retry of failed validations"
    )
    validation_retry_max_attempts: int = Field(
        default=3, description="Maximum number of validation retry attempts"
    )
    validation_retry_delay_seconds: int = Field(
        default=300, description="Delay between validation retry attempts (seconds)"
    )

    # --- BI Services Configuration ---
    # Settings for Apache Superset business intelligence dashboard
    # Services - Superset
    superset_port: int = Field(default=10007, description="Superset web port")
    superset_admin_user: str = Field(default="admin", description="Superset admin username")
    superset_admin_password: str = Field(default="admin", description="Superset admin password")
    superset_admin_email: str = Field(
        default="admin@example.com", description="Superset admin email"
    )

    # --- User Project Paths ---
    # Settings for user project structure (for installable package mode)
    workflows_path: str = Field(
        default="workflows",
        description="Path to user workflows directory (for external projects)",
    )
    dbt_project_dir: str = Field(
        default="workflows/transforms/dbt",
        description="Path to dbt project directory",
    )

    # --- Computed Paths ---
    # Dynamically determined paths based on container vs local environment
    # Paths (computed based on environment)
    @computed_field
    @property
    def dbt_profiles_dir(self) -> str:
        """dbt profiles directory - derived from dbt_project_dir."""
        return f"{self.dbt_project_dir}/profiles"

        # --- Orchestration Configuration ---

    # Settings for Dagster data orchestration platform
    # Dagster
    dagster_port: int = Field(default=10006, description="Dagster webserver port")
    phlo_force_in_process_executor: bool = Field(
        default=False, description="Force use of in-process executor"
    )
    phlo_force_multiprocess_executor: bool = Field(
        default=False, description="Force use of multiprocess executor"
    )
    phlo_host_platform: str | None = Field(
        default=None,
        description="Host platform for executor selection (Darwin/Linux/Windows). "
        "Auto-detected in CLI; set explicitly for daemon/webserver on macOS.",
    )

    # --- Hub Service Configuration ---
    # Settings for the Flask-based hub service
    # Hub
    app_port: int = Field(default=10009, description="Hub application port")
    flask_debug: bool = Field(default=False, description="Flask debug mode")

    # --- Alerting Configuration ---
    # Settings for alert integration (Slack, PagerDuty, Email)
    phlo_alert_slack_webhook: Optional[str] = Field(
        default=None, description="Slack incoming webhook URL"
    )
    phlo_alert_slack_channel: Optional[str] = Field(
        default=None, description="Default Slack channel for alerts"
    )
    phlo_alert_pagerduty_key: Optional[str] = Field(
        default=None, description="PagerDuty Events API v2 integration key"
    )
    phlo_alert_email_smtp_host: Optional[str] = Field(
        default=None, description="SMTP server hostname"
    )
    phlo_alert_email_smtp_port: int = Field(default=587, description="SMTP server port")
    phlo_alert_email_smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    phlo_alert_email_smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    phlo_alert_email_recipients: list[str] = Field(
        default_factory=list, description="Email recipients for alerts"
    )

    # --- OpenMetadata Configuration ---
    # Settings for OpenMetadata data catalog integration
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

    # --- dbt Configuration ---
    # Settings for dbt integration and manifest location
    dbt_manifest_path: str = Field(
        default="",
        description="Path to dbt manifest.json after running dbt docs generate",
    )
    dbt_catalog_path: str = Field(
        default="",
        description="Path to dbt catalog.json for column-level documentation",
    )

    def model_post_init(self, __context: object) -> None:
        if not self.dbt_manifest_path:
            self.dbt_manifest_path = f"{self.dbt_project_dir}/target/manifest.json"
        if not self.dbt_catalog_path:
            self.dbt_catalog_path = f"{self.dbt_project_dir}/target/catalog.json"

    # --- Nessie Configuration ---
    # Settings for Nessie catalog access
    nessie_api_version: str = Field(default="v1", description="Nessie API version")

    # --- Plugin Configuration ---
    # Settings for plugin system
    plugins_enabled: bool = Field(default=True, description="Enable plugin system")
    plugins_auto_discover: bool = Field(
        default=True,
        description="Automatically discover plugins from entry points on import",
    )
    plugins_whitelist: list[str] = Field(
        default_factory=list,
        description="Whitelist of plugin names to load (empty = all allowed)",
    )
    plugins_blacklist: list[str] = Field(
        default_factory=list, description="Blacklist of plugin names to exclude"
    )
    plugin_registry_url: str = Field(
        default="https://registry.phlo.dev/plugins.json",
        description="URL for the plugin registry catalog",
    )
    plugin_registry_cache_ttl_seconds: int = Field(
        default=3600, description="Registry cache TTL in seconds"
    )
    plugin_registry_timeout_seconds: int = Field(
        default=10, description="Registry fetch timeout in seconds"
    )

    # --- Logging Configuration ---
    phlo_log_level: str = Field(default="INFO", description="Default log level for Phlo")
    phlo_log_format: str = Field(
        default="json",
        description="Log format (json|console)",
    )
    phlo_log_router_enabled: bool = Field(
        default=True,
        description="Emit structured log events to the hook bus",
    )
    phlo_log_service_name: str = Field(
        default="phlo",
        description="Default service name for log records",
    )
    phlo_log_file_template: str = Field(
        default=".phlo/logs/{YMD}.log",
        description="Optional log file path template (empty to disable)",
    )

    # --- Computed Properties ---
    # Additional properties computed from the base settings
    @property
    def minio_endpoint(self) -> str:
        """Return MinIO endpoint in host:port form."""
        return f"{self.minio_host}:{self.minio_api_port}"

    @property
    def nessie_uri(self) -> str:
        """Return Nessie REST API URI for Iceberg catalog (base URL)."""
        return f"http://{self.nessie_host}:{self.nessie_port}/api"

    @property
    def nessie_api_v1_uri(self) -> str:
        """Return Nessie API v1 URI for direct API calls."""
        return f"http://{self.nessie_host}:{self.nessie_port}/api/v1"

    @property
    def nessie_iceberg_rest_uri(self) -> str:
        """
        Return Nessie REST catalog URI for Iceberg (without branch).

        The branch/tag is specified via the 'prefix' parameter when configuring
        the catalog, matching how Trino's iceberg.rest-catalog.prefix works.
        """
        return f"http://{self.nessie_host}:{self.nessie_port}/iceberg"

    @property
    def openmetadata_uri(self) -> str:
        """Return OpenMetadata API base URI."""
        return f"http://{self.openmetadata_host}:{self.openmetadata_port}/api"

    @property
    def openmetadata_database(self) -> str:
        """Return the OpenMetadata database name, defaulting to the Trino catalog."""
        return self.openmetadata_database_name or self.trino_catalog

    # --- Helper Methods ---

    # Methods to generate connection strings and catalog configurations
    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        """
        Get the S3 warehouse path for a specific Nessie branch.

        Args:
            branch: Nessie branch name (default: main)

        Returns:
            S3 warehouse path for the branch

        Example:
            config.get_iceberg_warehouse_for_branch("dev")
            # Returns: "s3://lake/warehouse"

        Note:
            Nessie manages branch isolation internally via the prefix parameter.
            All branches share the same physical warehouse location.
        """
        return self.iceberg_warehouse_path

    def get_pyiceberg_catalog_config(self, ref: str = "main") -> dict:
        """
        Get PyIceberg catalog configuration for a specific Nessie branch/tag.

        Args:
            ref: Nessie branch or tag name (default: main)

        Returns:
            Dictionary of catalog configuration parameters for PyIceberg

        Example:
            config.get_pyiceberg_catalog_config("dev")
            # Returns config dict that can be passed to load_catalog(**config)

        Note:
            The Nessie REST catalog uses the branch name in the URI path.
            When PyIceberg calls http://nessie:19120/iceberg/{ref}/v1/config,
            Nessie returns a configuration with prefix set to the branch name,
            and all subsequent API calls use /v1/{prefix}/ endpoints.
        """
        return {
            "type": "rest",
            "uri": f"{self.nessie_iceberg_rest_uri}/{ref}",  # Branch in URI path
            # S3/MinIO configuration
            "s3.endpoint": f"http://{self.minio_host}:{self.minio_api_port}",
            "s3.access-key-id": self.minio_root_user,
            "s3.secret-access-key": self.minio_root_password,
            "s3.path-style-access": "true",
            "s3.region": "us-east-1",
        }

    @property
    def trino_connection_string(self) -> str:
        """Return Trino connection string for SQLAlchemy/dbt."""
        return f"trino://{self.trino_host}:{self.trino_port}/{self.trino_catalog}"

    @property
    def dbt_project_path(self) -> Path:
        """Return dbt project directory as Path object."""
        return Path(self.dbt_project_dir)

    @property
    def dbt_profiles_path(self) -> Path:
        """Return dbt profiles directory as Path object."""
        return Path(self.dbt_profiles_dir)

    def get_postgres_connection_string(self, include_db: bool = True) -> str:
        """
        Construct PostgreSQL connection string.

        Args:
            include_db: If True, include database name in connection string

        Returns:
            PostgreSQL connection string
        """
        db_part = f"/{self.postgres_db}" if include_db else ""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}{db_part}"
        )


# --- Global Configuration Instance ---
# Cached configuration instance for application-wide use
@lru_cache
def _get_config() -> Settings:
    """
    Get cached config instance.

    Uses lru_cache to ensure config is loaded once and reused.

    Returns:
        Validated Settings instance
    """
    return Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    This is the recommended way to access configuration in new code,
    as it's easier to test and allows for future dependency injection.

    Returns:
        Validated Settings instance

    Example:
        ```python
        from phlo.config import get_settings

        settings = get_settings()
        workflows_path = settings.workflows_path
        ```
    """
    return _get_config()


# Global config instance for convenient access throughout the application
# Note: Consider using get_settings() in new code for better testability
config = _get_config()
