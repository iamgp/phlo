from __future__ import annotations

from dataclasses import dataclass

from lakehousekit.config import config


@dataclass(frozen=True)
class DuckLakeRuntimeConfig:
    """Runtime configuration required to attach to DuckLake via DuckDB."""

    catalog_alias: str
    catalog_database: str
    data_path: str
    default_dataset: str
    staging_dataset: str
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    minio_endpoint: str
    minio_region: str
    minio_access_key: str
    minio_secret_key: str
    minio_use_ssl: bool
    s3_url_style: str = "path"
    ducklake_retry_count: int = 100
    ducklake_retry_wait_ms: int = 100
    ducklake_retry_backoff: float = 2.0

    @property
    def postgres_secret_name(self) -> str:
        return f"{self.catalog_alias}_postgres_secret"

    @property
    def s3_secret_name(self) -> str:
        return f"{self.catalog_alias}_s3_secret"

    @property
    def ducklake_secret_name(self) -> str:
        return f"{self.catalog_alias}_ducklake_secret"


def build_ducklake_runtime_config(
    *,
    default_dataset: str | None = None,
    staging_dataset: str | None = None,
) -> DuckLakeRuntimeConfig:
    """
    Build a DuckLake runtime configuration from global settings.

    Args:
        default_dataset: Optional override for the primary dataset/schema.
        staging_dataset: Optional override for the staging dataset used by loaders.

    Returns:
        DuckLakeRuntimeConfig with derived values.
    """

    dataset = default_dataset or config.ducklake_default_dataset
    staging = staging_dataset or f"{dataset}_staging"

    return DuckLakeRuntimeConfig(
        catalog_alias=config.ducklake_catalog_alias,
        catalog_database=config.ducklake_catalog_database,
        data_path=config.ducklake_data_path,
        default_dataset=dataset,
        staging_dataset=staging,
        postgres_host=config.postgres_host,
        postgres_port=config.postgres_port,
        postgres_user=config.postgres_user,
        postgres_password=config.postgres_password,
        minio_endpoint=config.minio_endpoint,
        minio_region=config.ducklake_region,
        minio_access_key=config.minio_root_user,
        minio_secret_key=config.minio_root_password,
        minio_use_ssl=config.ducklake_use_ssl,
    )
