"""Iceberg settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo_minio.settings import get_settings as get_minio_settings
from phlo_nessie.settings import get_settings as get_nessie_settings


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

    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        return self.iceberg_warehouse_path

    def get_pyiceberg_catalog_config(self, ref: str = "main") -> dict:
        nessie_settings = get_nessie_settings()
        minio_settings = get_minio_settings()
        return {
            "type": "rest",
            "uri": f"{nessie_settings.nessie_iceberg_rest_uri()}/{ref}",
            "warehouse": self.get_iceberg_warehouse_for_branch(ref),
            "s3.endpoint": f"http://{minio_settings.minio_host}:{minio_settings.minio_api_port}",
            "s3.access-key-id": minio_settings.minio_root_user,
            "s3.secret-access-key": minio_settings.minio_root_password,
            "s3.path-style-access": "true",
            "s3.region": minio_settings.s3_region,
        }


@lru_cache(maxsize=1)
def get_settings() -> IcebergSettings:
    return IcebergSettings()
