import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for cascade using environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Database - Postgres
    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="lake", description="PostgreSQL username")
    postgres_password: str = Field(description="PostgreSQL password")
    postgres_db: str = Field(default="lakehouse", description="PostgreSQL database name")
    postgres_mart_schema: str = Field(
        default="marts", description="Schema for published mart tables"
    )

    # Storage - MinIO
    minio_host: str = Field(default="minio", description="MinIO service hostname")
    minio_root_user: str = Field(default="minio", description="MinIO root username")
    minio_root_password: str = Field(description="MinIO root password")
    minio_api_port: int = Field(default=9000, description="MinIO API port")
    minio_console_port: int = Field(default=9001, description="MinIO console port")

    # Catalog - Nessie
    nessie_version: str = Field(default="0.105.5", description="Nessie version")
    nessie_port: int = Field(default=19120, description="Nessie REST API port")
    nessie_host: str = Field(default="nessie", description="Nessie service hostname")

    # Query Engine - Trino
    trino_version: str = Field(default="477", description="Trino version")
    trino_port: int = Field(default=8080, description="Trino HTTP port")
    trino_host: str = Field(default="trino", description="Trino service hostname")
    trino_catalog: str = Field(default="iceberg", description="Trino catalog name for Iceberg")

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

    # Services - Superset
    superset_port: int = Field(default=8088, description="Superset web port")
    superset_admin_user: str = Field(default="admin", description="Superset admin username")
    superset_admin_password: str = Field(description="Superset admin password")
    superset_admin_email: str = Field(
        default="admin@example.com", description="Superset admin email"
    )

    # Paths (computed based on environment)
    @computed_field
    @property
    def dbt_project_dir(self) -> str:
        """dbt project directory - /dbt in container, transforms/dbt locally."""
        if os.path.exists("/dbt"):  # Container environment
            return "/dbt"
        else:  # Local development
            return "transforms/dbt"

    @computed_field
    @property
    def dbt_profiles_dir(self) -> str:
        """dbt profiles directory - /dbt/profiles in container, transforms/dbt/profiles locally."""
        if os.path.exists("/dbt"):  # Container environment
            return "/dbt/profiles"
        else:  # Local development
            return "transforms/dbt/profiles"

    # Dagster
    dagster_port: int = Field(default=3000, description="Dagster webserver port")
    cascade_force_in_process_executor: bool = Field(
        default=False, description="Force use of in-process executor"
    )
    cascade_force_multiprocess_executor: bool = Field(
        default=False, description="Force use of multiprocess executor"
    )

    # Hub
    app_port: int = Field(default=54321, description="Hub application port")
    flask_debug: bool = Field(default=False, description="Flask debug mode")

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


@lru_cache
def _get_config() -> Settings:
    """
    Get cached config instance.

    Uses lru_cache to ensure config is loaded once and reused.

    Returns:
        Validated Settings instance
    """
    return Settings()


# Global config instance for convenient access throughout the application
config = _get_config()
