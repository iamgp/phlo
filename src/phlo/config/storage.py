from pydantic import Field

from phlo.config.base import BaseConfig


class StorageConfig(BaseConfig):
    """MinIO S3-compatible object storage configuration."""

    minio_host: str = Field(default="minio", description="MinIO service hostname")
    minio_root_user: str = Field(default="minio", description="MinIO root username")
    minio_root_password: str = Field(..., description="MinIO root password")
    minio_api_port: int = Field(default=10001, description="MinIO API port")
    minio_console_port: int = Field(default=10002, description="MinIO console port")

    @property
    def minio_endpoint(self) -> str:
        """Return MinIO endpoint in host:port form."""
        return f"{self.minio_host}:{self.minio_api_port}"
