"""ClickHouse settings configuration.

This module provides Pydantic-based configuration management for ClickHouse
connection parameters, including host, port, authentication, and security settings.

Example:
    Loading ClickHouse settings:

    >>> from phlo_clickhouse.settings import get_settings, ClickHouseSettings
    >>> settings = get_settings()
    >>> settings.clickhouse_host
    'clickhouse'


    Service settings for ClickHouse, built on the shared phlo.config base/cache/network helpers.
    Loaded within phlo_clickhouse by plugin and resource code through get_settings().
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.network import resolve_host


class ClickHouseSettings(BaseConfig):
    """ClickHouse data plane configuration model.

    Configuration class for ClickHouse connection parameters using Pydantic
    for validation and default value management.

    Attributes:
        clickhouse_host: Hostname or IP address of the ClickHouse server.
            Defaults to "clickhouse" for Docker Compose networking.
        clickhouse_http_port: HTTP interface port for ClickHouse.
            Defaults to 8123 (standard ClickHouse HTTP port).
        clickhouse_native_port: Native protocol port for ClickHouse.
            Defaults to 19000.
        clickhouse_user: Username for ClickHouse authentication.
            Defaults to "default".
        clickhouse_password: Password for ClickHouse authentication.
            Defaults to empty string for unauthenticated connections.
        clickhouse_db: Default database to connect to.
            Defaults to "default".
        clickhouse_secure: Whether to use TLS/SSL for connections.
            Defaults to False.

    Example:
        >>> settings = ClickHouseSettings(
        ...     clickhouse_host="localhost",
        ...     clickhouse_db="analytics"
        ... )
        >>> settings.clickhouse_http_endpoint()
        'localhost:8123'

    """

    clickhouse_host: str = Field(default="clickhouse", description="ClickHouse service hostname")
    clickhouse_http_port: int = Field(default=8123, description="ClickHouse HTTP interface port")
    clickhouse_native_port: int = Field(
        default=19000, description="ClickHouse native protocol port"
    )
    clickhouse_user: str = Field(default="default", description="ClickHouse username")
    clickhouse_password: str = Field(default="", description="ClickHouse password")
    clickhouse_db: str = Field(default="default", description="Default ClickHouse database")
    clickhouse_secure: bool = Field(default=False, description="Use TLS for ClickHouse connections")

    def model_post_init(self, __context: object) -> None:
        host, port = resolve_host(
            self.clickhouse_host,
            self.clickhouse_http_port,
            port_env_var="CLICKHOUSE_HTTP_PORT",
        )
        object.__setattr__(self, "clickhouse_host", host)
        object.__setattr__(self, "clickhouse_http_port", port)

    def clickhouse_http_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse HTTP interface.

        Returns:
            Formatted endpoint string "host:port" for HTTP connections.

        Example:
            >>> settings = ClickHouseSettings(clickhouse_host="localhost", clickhouse_http_port=8123)
            >>> settings.clickhouse_http_endpoint()
            'localhost:8123'

        """
        return f"{self.clickhouse_host}:{self.clickhouse_http_port}"

    def clickhouse_native_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse native interface.

        Returns:
            Formatted endpoint string "host:port" for native protocol connections.

        Example:
            >>> settings = ClickHouseSettings(clickhouse_host="localhost", clickhouse_native_port=9000)
            >>> settings.clickhouse_native_endpoint()
            'localhost:9000'

        """
        return f"{self.clickhouse_host}:{self.clickhouse_native_port}"


@project_root_cached
def get_settings(project_root: Path) -> ClickHouseSettings:
    """Return cached ClickHouse settings for the selected project root.

    Settings are cached per resolved project root, with up to 16 entries,
    and reused across the application lifecycle.

    Args:
        project_root: Resolved project root used for cache selection.

    Returns:
        ClickHouseSettings instance with loaded configuration.

    Example:
        >>> settings = get_settings()
        >>> settings.clickhouse_host
        'clickhouse'
        >>> # Subsequent calls for the same root return the same cached instance
        >>> get_settings() is settings
        True

    """
    return ClickHouseSettings()
