"""ClickHouse settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from phlo.config.base import BaseConfig


class ClickHouseSettings(BaseConfig):
    """ClickHouse data plane configuration."""

    clickhouse_host: str = Field(default="clickhouse", description="ClickHouse service hostname")
    clickhouse_http_port: int = Field(default=8123, description="ClickHouse HTTP interface port")
    clickhouse_native_port: int = Field(default=9000, description="ClickHouse native protocol port")
    clickhouse_user: str = Field(default="default", description="ClickHouse username")
    clickhouse_password: str = Field(default="", description="ClickHouse password")
    clickhouse_db: str = Field(default="default", description="Default ClickHouse database")
    clickhouse_secure: bool = Field(default=False, description="Use TLS for ClickHouse connections")

    def clickhouse_http_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse HTTP interface."""
        return f"{self.clickhouse_host}:{self.clickhouse_http_port}"

    def clickhouse_native_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse native interface."""
        return f"{self.clickhouse_host}:{self.clickhouse_native_port}"


@lru_cache(maxsize=1)
def get_settings() -> ClickHouseSettings:
    """Return cached ClickHouse settings."""
    return ClickHouseSettings()
