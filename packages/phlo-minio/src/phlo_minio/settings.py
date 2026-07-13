"""MinIO settings module for S3-compatible storage configuration.

This module provides configuration management for MinIO connections,
including host resolution, port configuration, and S3-compatible settings.

Examples:
    Get cached settings instance:
        >>> from phlo_minio.settings import get_settings
        >>> settings = get_settings()
        >>> endpoint = settings.minio_endpoint()

    Create custom settings:
        >>> from phlo_minio.settings import MinioSettings
        >>> settings = MinioSettings(
        ...     minio_host="custom-minio",
        ...     minio_api_port=9000,
        ...     minio_root_user="admin",
        ...     minio_root_password="secretpass"
        ... )

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.network import resolve_host


class MinioSettings(BaseConfig):
    """Configuration class for MinIO S3-compatible storage.

    Provides settings for MinIO connection including host, credentials,
    ports, and S3 region configuration. Supports environment-based
    host resolution for Docker Compose and local development.

    Attributes:
        minio_host: MinIO service hostname (default: "minio").
        minio_root_user: Root username for MinIO authentication.
        minio_root_password: Root password for MinIO authentication.
        minio_api_port: Port for S3 API operations.
        minio_console_port: Port for MinIO web console.
        s3_region: AWS S3-compatible region identifier.

    Examples:
        Default configuration:
            >>> settings = MinioSettings()
            >>> print(settings.minio_host)
            'minio'
            >>> print(settings.s3_region)
            'us-east-1'

        Custom endpoint configuration:
            >>> settings = MinioSettings(minio_host="localhost", minio_api_port=9000)
            >>> print(settings.minio_endpoint())
            'localhost:9000'

        Environment-based resolution:
            # With MINIO_API_PORT=9001 in environment:
            >>> settings = MinioSettings()
            >>> print(settings.minio_api_port)  # Resolved from env
            9001

    Note:
        The model_post_init method automatically resolves host and port
        from environment variables when available.

    """

    minio_host: str = Field(default="minio", description="MinIO service hostname")
    minio_root_user: str = Field(default="minio", description="MinIO root username")
    minio_root_password: str = Field(default="minio123", description="MinIO root password")
    minio_api_port: int = Field(default=10001, description="MinIO API port")
    minio_console_port: int = Field(default=10002, description="MinIO console port")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    def model_post_init(self, __context: Any) -> None:
        """Resolve host and port from environment variables if available.

        Updates the minio_host and minio_api_port attributes based on
        environment configuration. This enables Docker Compose service
        discovery and local development overrides.

        Args:
            __context: Pydantic internal context (unused).

        Examples:
            Automatic host resolution:
                # With MINIO_HOST=localhost in environment
                >>> settings = MinioSettings()
                >>> settings.minio_host  # Resolved to 'localhost'
                'localhost'

        Note:
            Uses phlo.config.network.resolve_host for environment-based
            resolution. The port_env_var parameter enables port override
            via MINIO_API_PORT environment variable.

        """
        host, port = resolve_host(
            self.minio_host, self.minio_api_port, port_env_var="MINIO_API_PORT"
        )
        object.__setattr__(self, "minio_host", host)
        object.__setattr__(self, "minio_api_port", port)

    def minio_endpoint(self) -> str:
        """Return the MinIO API endpoint as host:port string.

        Returns:
            str: Formatted endpoint string (e.g., "minio:10001").

        Examples:
            Default endpoint:
                >>> settings = MinioSettings()
                >>> settings.minio_endpoint()
                'minio:10001'

            Custom endpoint:
                >>> settings = MinioSettings(minio_host="localhost", minio_api_port=9000)
                >>> settings.minio_endpoint()
                'localhost:9000'

        Use Case:
            Use this endpoint for S3 client configuration:
                >>> import boto3
                >>> s3 = boto3.client(
                ...     's3',
                ...     endpoint_url=f"http://{settings.minio_endpoint()}",
                ...     aws_access_key_id=settings.minio_root_user,
                ...     aws_secret_access_key=settings.minio_root_password
                ... )

        """
        return f"{self.minio_host}:{self.minio_api_port}"


@project_root_cached
def get_settings(project_root: Path) -> MinioSettings:
    """Return a cached MinIO settings instance.

    Creates and caches a single MinioSettings instance to avoid
    repeated environment resolution and configuration loading.
    The cache ensures consistent settings across the application
    lifecycle.

    Returns:
        MinioSettings: Cached settings instance.

    Examples:
        Singleton pattern:
            >>> settings1 = get_settings()
            >>> settings2 = get_settings()
            >>> settings1 is settings2  # Same instance
            True

        Accessing configuration:
            >>> settings = get_settings()
            >>> endpoint = settings.minio_endpoint()
            >>> print(f"MinIO at {endpoint}")
            MinIO at minio:10001

        Integration with S3 clients:
            >>> settings = get_settings()
            >>> s3_config = {
            ...     'endpoint_url': f"http://{settings.minio_endpoint()}",
            ...     'aws_access_key_id': settings.minio_root_user,
            ...     'aws_secret_access_key': settings.minio_root_password,
            ...     'region_name': settings.s3_region
            ... }

    Warning:
        Settings are cached for the process lifetime. To refresh
        settings, restart the application process.

    """
    return MinioSettings()
