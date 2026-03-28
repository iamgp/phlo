"""MinIO settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.network import resolve_host


class MinioSettings(BaseConfig):
    """MinIO S3-compatible storage configuration."""

    minio_host: str = Field(default="minio", description="MinIO service hostname")
    minio_root_user: str = Field(default="minio", description="MinIO root username")
    minio_root_password: str = Field(default="minio123", description="MinIO root password")
    minio_api_port: int = Field(default=10001, description="MinIO API port")
    minio_console_port: int = Field(default=10002, description="MinIO console port")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    def model_post_init(self, __context: Any) -> None:
        host, port = resolve_host(
            self.minio_host, self.minio_api_port, port_env_var="MINIO_API_PORT"
        )
        object.__setattr__(self, "minio_host", host)
        object.__setattr__(self, "minio_api_port", port)

    def minio_endpoint(self) -> str:
        """Return host:port endpoint for MinIO API."""
        return f"{self.minio_host}:{self.minio_api_port}"


@lru_cache(maxsize=1)
def get_settings() -> MinioSettings:
    """Return cached MinIO settings."""
    return MinioSettings()
