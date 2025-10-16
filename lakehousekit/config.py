from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for lakehousekit using environment variables."""

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

    # Storage - DuckLake
    ducklake_catalog_database: str = Field(
        default="ducklake_catalog",
        description="PostgreSQL database storing DuckLake catalog metadata",
    )
    ducklake_catalog_alias: str = Field(
        default="dbt",
        description="Alias used when attaching the DuckLake catalog in DuckDB",
    )
    ducklake_data_bucket: str = Field(
        default="lake", description="Object store bucket for DuckLake data files"
    )
    ducklake_data_prefix: str = Field(
        default="ducklake",
        description="Prefix within the DuckLake data bucket for managed tables",
    )
    ducklake_default_dataset: str = Field(
        default="raw",
        description="Default dataset/schema used by ingestion jobs inside DuckLake",
    )
    ducklake_region: str = Field(
        default="eu-west-1",
        description="Region identifier used for DuckLake S3/MinIO connections",
    )
    ducklake_use_ssl: bool = Field(
        default=False,
        description="Whether DuckLake should use SSL when talking to object storage",
    )

    # Services - Superset
    superset_port: int = Field(default=8088, description="Superset web port")
    superset_admin_user: str = Field(default="admin", description="Superset admin username")
    superset_admin_password: str = Field(description="Superset admin password")
    superset_admin_email: str = Field(
        default="admin@example.com", description="Superset admin email"
    )

    # Paths
    dbt_project_dir: str = Field(default="/dbt", description="dbt project directory")
    dbt_profiles_dir: str = Field(default="/dbt/profiles", description="dbt profiles directory")

    # Dagster
    dagster_port: int = Field(default=3000, description="Dagster webserver port")
    lakehousekit_force_in_process_executor: bool = Field(
        default=False, description="Force use of in-process executor"
    )
    lakehousekit_force_multiprocess_executor: bool = Field(
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
    def ducklake_data_path(self) -> str:
        """Return fully-qualified DuckLake data path."""
        prefix = self.ducklake_data_prefix.strip("/")
        if prefix:
            return f"s3://{self.ducklake_data_bucket}/{prefix}"
        return f"s3://{self.ducklake_data_bucket}"

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
