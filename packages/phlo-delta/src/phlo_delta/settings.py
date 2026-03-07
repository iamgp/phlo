"""Delta Lake settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class DeltaSettings(BaseConfig):
    """Delta Lake storage configuration."""

    delta_warehouse_path: str = Field(
        default="s3://lake/warehouse/delta", description="S3 path for Delta tables"
    )
    delta_staging_path: str = Field(
        default="s3://lake/stage", description="S3 path for staging parquet files"
    )
    delta_default_namespace: str = Field(
        default="raw", description="Default namespace/schema for Delta tables"
    )
    delta_s3_endpoint: str | None = Field(
        default="http://minio:10001",
        description="S3 endpoint URL for Delta I/O",
    )
    delta_s3_access_key: str = Field(
        default="minio",
        description="S3 access key for Delta I/O",
    )
    delta_s3_secret_key: str = Field(
        default="minio123",
        description="S3 secret key for Delta I/O",
    )
    delta_s3_region: str = Field(
        default="us-east-1",
        description="S3 region for Delta I/O",
    )
    delta_s3_allow_unsafe_rename: bool = Field(
        default=True,
        description="Allow unsafe rename for S3 (non-HDFS) backends",
    )

    def get_storage_options(self) -> dict[str, str]:
        """Build deltalake storage options dict for S3 access.

        Returns:
            dict[str, str]: Storage options compatible with deltalake I/O.
        """
        opts: dict[str, str] = {
            "AWS_ACCESS_KEY_ID": self.delta_s3_access_key,
            "AWS_SECRET_ACCESS_KEY": self.delta_s3_secret_key,
            "AWS_REGION": self.delta_s3_region,
            "AWS_ALLOW_HTTP": "true",
        }
        if self.delta_s3_endpoint:
            opts["AWS_ENDPOINT_URL"] = self.delta_s3_endpoint
        if self.delta_s3_allow_unsafe_rename:
            opts["AWS_S3_ALLOW_UNSAFE_RENAME"] = "true"
        return opts


@lru_cache(maxsize=1)
def get_settings() -> DeltaSettings:
    """Get cached Delta Lake settings.

    Returns:
        DeltaSettings: Cached Delta Lake settings instance.
    """
    return DeltaSettings()
