"""PostgreSQL connection settings and configuration.

This module provides Pydantic-based settings management for PostgreSQL connections,
including support for connection string generation and host/port resolution via
the phlo configuration system.

Example:
    >>> from phlo_postgres.settings import get_settings
    >>> settings = get_settings()
    >>> conn_str = settings.get_postgres_connection_string()
    >>> print(conn_str)
    postgresql://phlo:phlo@postgres:5432/phlo


    Settings for the PostgreSQL service, built on the shared phlo.config base/cache/network helpers.
    Loaded lazily via get_settings(); phlo_sling pulls its Postgres connection settings at runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.network import resolve_host


class PostgresSettings(BaseConfig):
    """PostgreSQL database connection and schema configuration.

    Configuration class that manages PostgreSQL connection parameters using
    Pydantic validation. Supports environment variable overrides and provides
    utilities for building connection strings.

    Attributes:
        postgres_host: Database server hostname. Can be resolved via environment
            variables and supports special host resolution rules.
        postgres_port: Database server port number.
        postgres_user: Authentication username.
        postgres_password: Authentication password (URL-encoded in connection strings).
        postgres_db: Default database name to connect to.
        postgres_mart_schema: Schema name for published data mart tables.

    Example:
        >>> settings = PostgresSettings()
        >>> print(settings.postgres_host)
        postgres
        >>> conn_str = settings.get_postgres_connection_string()
        >>> print(conn_str)
        postgresql://phlo:phlo@postgres:5432/phlo
        >>>
        >>> # Override defaults
        >>> custom = PostgresSettings(
        ...     postgres_host="prod.db.internal",
        ...     postgres_user="admin",
        ...     postgres_password="secret123"
        ... )

    """

    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="phlo", description="PostgreSQL username")
    postgres_password: str = Field(default="phlo", description="PostgreSQL password")
    postgres_db: str = Field(default="phlo", description="PostgreSQL database name")
    postgres_mart_schema: str = Field(
        default="marts", description="Schema for published mart tables"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook for host and port resolution.

        Resolves the postgres_host and postgres_port values using phlo's
        network resolution system. This allows for dynamic host resolution
        based on environment variables (e.g., POSTGRES_PORT for test overrides).

        Args:
            __context: Pydantic model context (unused but required by signature).

        Note:
            Uses object.__setattr__ to bypass Pydantic's frozen model behavior.
            This ensures the resolved values are stored after initial validation.

        """
        host, port = resolve_host(
            self.postgres_host, self.postgres_port, port_env_var="POSTGRES_PORT"
        )
        object.__setattr__(self, "postgres_host", host)
        object.__setattr__(self, "postgres_port", port)

    def get_postgres_connection_string(self, include_db: bool = True) -> str:
        """Build a PostgreSQL connection URI from current settings.

        Constructs a properly URL-encoded PostgreSQL connection string suitable
        for use with SQLAlchemy, psycopg2, or other database libraries.

        Args:
            include_db: Whether to include the database name in the connection
                string. Set to False when connecting to the server to create
                the database, or when the database name is specified separately.

        Returns:
            str: URL-encoded PostgreSQL connection string.

        Example:
            >>> settings = PostgresSettings()
            >>> settings.get_postgres_connection_string()
            'postgresql://phlo:phlo@postgres:5432/phlo'
            >>>
            >>> # Without database (for server-level operations)
            >>> settings.get_postgres_connection_string(include_db=False)
            'postgresql://phlo:phlo@postgres:5432'
            >>>
            >>> # With special characters in password
            >>> settings = PostgresSettings(postgres_password="p@ssw/rd")
            >>> settings.get_postgres_connection_string()
            'postgresql://phlo:p%40ssw%2Frd@postgres:5432/phlo'

        """
        db_part = f"/{self.postgres_db}" if include_db else ""
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql://{user}:{password}@{self.postgres_host}:{self.postgres_port}{db_part}"


@project_root_cached
def get_settings(project_root: Path) -> PostgresSettings:
    """Return cached PostgreSQL settings for the selected project root.

    Settings are cached per resolved project root, with up to 16 entries,
    to avoid repeated parsing while isolating project configuration.

    Args:
        project_root: Resolved project root used for cache selection.

    Returns:
        PostgresSettings: Cached settings instance.

    Note:
        Calls for the same project root return the same settings object.
        Call ``get_settings.cache_clear()`` after changing configuration.

    Example:
        >>> settings1 = get_settings()
        >>> settings2 = get_settings()
        >>> settings1 is settings2  # Same cached instance for this root
        True
        >>>
        >>> # Access connection parameters
        >>> settings = get_settings()
        >>> print(f"Connecting to {settings.postgres_host}:{settings.postgres_port}")

    """
    return PostgresSettings()
