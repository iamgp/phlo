"""RustFS settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class RustfsSettings(BaseConfig):
    """RustFS S3-compatible storage configuration."""

    rustfs_host: str = Field(default="rustfs", description="RustFS service hostname")
    rustfs_access_key: str = Field(default="rustfsadmin", description="RustFS access key")
    rustfs_secret_key: str = Field(default="rustfsadmin", description="RustFS secret key")
    rustfs_api_port: int = Field(default=9000, description="RustFS S3 API port")
    rustfs_console_port: int = Field(default=9001, description="RustFS console port")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    def rustfs_endpoint(self) -> str:
        """Return host:port endpoint for RustFS S3 API."""
        return f"{self.rustfs_host}:{self.rustfs_api_port}"


@lru_cache(maxsize=1)
def get_settings() -> RustfsSettings:
    """Return cached RustFS settings."""
    return RustfsSettings()
