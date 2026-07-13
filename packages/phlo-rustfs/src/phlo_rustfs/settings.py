"""RustFS settings.

This module defines the configuration schema and defaults for connecting to
RustFS (S3-compatible object storage). Settings are loaded from environment
variables and validated using Pydantic.

Classes:
    RustfsSettings: Pydantic configuration model for RustFS connectivity.

Functions:
    get_settings: Returns a cached RustfsSettings instance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.network import resolve_host


class RustfsSettings(BaseConfig):
    """RustFS S3-compatible storage configuration.

    Pydantic configuration model for RustFS connectivity. Settings are loaded
    from environment variables with sensible defaults for local development.

    Attributes:
        rustfs_host: Service hostname for RustFS container (default: "rustfs").
        rustfs_access_key: Access key for S3 API authentication (default: "rustfsadmin").
        rustfs_secret_key: Secret key for S3 API authentication (default: "rustfsadmin").
        rustfs_api_port: Port for S3-compatible API endpoint (default: 9000).
        rustfs_console_port: Port for web management console (default: 9001).
        s3_region: AWS-style region identifier (default: "us-east-1").

    Example:
        >>> settings = RustfsSettings()
        >>> print(settings.rustfs_endpoint())
        "localhost:9000"

    """

    rustfs_host: str = Field(default="rustfs", description="RustFS service hostname")
    rustfs_access_key: str = Field(default="rustfsadmin", description="RustFS access key")
    rustfs_secret_key: str = Field(default="rustfsadmin", description="RustFS secret key")
    rustfs_api_port: int = Field(default=9000, description="RustFS S3 API port")
    rustfs_console_port: int = Field(default=9001, description="RustFS console port")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    def model_post_init(self, __context: Any) -> None:
        """Resolve host and port after model initialization.

        Applies host resolution logic using phlo.config.network.resolve_host.
        Updates rustfs_host and rustfs_api_port based on environment variables
        and DNS resolution. Uses object.__setattr__ to bypass Pydantic's
        immutability protections for post-initialization modifications.

        Args:
            __context: Pydantic internal context (unused).

        """
        host, port = resolve_host(
            self.rustfs_host, self.rustfs_api_port, port_env_var="RUSTFS_API_PORT"
        )
        object.__setattr__(self, "rustfs_host", host)
        object.__setattr__(self, "rustfs_api_port", port)

    def rustfs_endpoint(self) -> str:
        """Return host:port endpoint for RustFS S3 API.

        Formats the resolved host and API port into a standard endpoint
        string suitable for S3 SDK configuration.

        Returns:
            String in format "host:port" for the S3 API endpoint.

        Example:
            >>> settings = RustfsSettings()
            >>> settings.rustfs_endpoint()
            "localhost:9000"

        """
        return f"{self.rustfs_host}:{self.rustfs_api_port}"


@project_root_cached
def get_settings(project_root: Path) -> RustfsSettings:
    """Return cached RustFS settings for the selected project root.

    Settings are cached per resolved project root, with up to 16 entries,
    improving performance while keeping project configuration isolated.

    Args:
        project_root: Resolved project root used for cache selection.

    Returns:
        Cached RustfsSettings instance for the selected root.

    Example:
        >>> settings = get_settings()
        >>> same_settings = get_settings()
        >>> settings is same_settings
        True

    """
    return RustfsSettings()
