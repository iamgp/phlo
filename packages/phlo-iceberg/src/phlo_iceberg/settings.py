"""Iceberg settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class IcebergSettings(BaseConfig):
    """Iceberg catalog configuration."""

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
    iceberg_s3_endpoint: str | None = Field(
        default="http://minio:10001",
        description="S3 endpoint URL for Iceberg I/O",
    )
    iceberg_s3_access_key: str = Field(
        default="minio",
        description="S3 access key for Iceberg I/O",
    )
    iceberg_s3_secret_key: str = Field(
        default="minio123",
        description="S3 secret key for Iceberg I/O",
    )
    iceberg_s3_region: str = Field(
        default="us-east-1",
        description="S3 region for Iceberg I/O",
    )
    iceberg_nessie_uri: str = Field(
        default="http://nessie:19120/iceberg",
        description="Nessie Iceberg REST endpoint base URI",
    )

    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        """Get the warehouse path for a branch.

        Args:
            branch: Nessie branch name.

        Returns:
            str: Warehouse path for the requested branch.
        """
        return self.iceberg_warehouse_path

    def get_pyiceberg_catalog_config(self, ref: str = "main") -> dict:
        """Build PyIceberg REST catalog configuration.

        Args:
            ref: Nessie reference to target.

        Returns:
            dict: PyIceberg catalog configuration values.
        """
        return {
            "type": "rest",
            "uri": f"{self.iceberg_nessie_uri}/{ref}",
            "warehouse": self.get_iceberg_warehouse_for_branch(ref),
            "s3.endpoint": self.iceberg_s3_endpoint,
            "s3.access-key-id": self.iceberg_s3_access_key,
            "s3.secret-access-key": self.iceberg_s3_secret_key,
            "s3.path-style-access": "true",
            "s3.region": self.iceberg_s3_region,
        }


@lru_cache(maxsize=1)
def get_settings() -> IcebergSettings:
    """Get cached Iceberg settings.

    Returns:
        IcebergSettings: Cached Iceberg settings instance.
    """
    return IcebergSettings()
