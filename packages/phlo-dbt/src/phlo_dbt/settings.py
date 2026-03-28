"""dbt settings and configuration management.

This module provides Pydantic-based configuration management for dbt integration
within the Phlo platform. It handles query engine settings, project paths, and
derived artifact locations.

Example:
    >>> from phlo_dbt.settings import get_settings, DbtSettings
    >>> settings = get_settings()
    >>> print(f"Project: {settings.dbt_project_path}")
    >>> print(f"Catalog: {settings.dbt_query_catalog}")
    >>>
    >>> # Create custom settings
    >>> custom = DbtSettings(dbt_query_catalog="analytics", dbt_query_threads=8)

"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field

from phlo.config.base import BaseConfig


class DbtSettings(BaseConfig):
    """dbt project configuration settings.

    Pydantic-based configuration class that manages all dbt-related settings
    including query engine connection parameters, project paths, and artifact
    locations. Uses environment variables and .env files for configuration.

    Attributes:
        dbt_query_engine_type: Query engine adapter type (default: "trino").
        dbt_query_host: Query engine hostname (default: "trino").
        dbt_query_port: Query engine port (default: 8080).
        dbt_query_catalog: Base catalog name (default: "iceberg").
        dbt_query_schema: Default schema (default: "raw").
        dbt_query_user: Database user (default: "dagster").
        dbt_query_http_scheme: HTTP scheme (default: "http").
        dbt_query_auth_method: Auth method (default: "none").
        dbt_query_threads: Parallel threads (default: 2).
        dbt_project_dir: Path to dbt project directory (default: "workflows/transforms/dbt").
        dbt_manifest_path: Path to manifest.json (auto-derived if empty).
        dbt_catalog_path: Path to catalog.json (auto-derived if empty).

    Example:
        >>> settings = DbtSettings(
        ...     dbt_query_catalog="analytics",
        ...     dbt_query_threads=8,
        ...     dbt_project_dir="custom/path"
        ... )
        >>> print(settings.dbt_project_path)
        PosixPath('custom/path')
        >>> print(settings.dbt_profiles_path)
        PosixPath('custom/path/profiles')

    """

    dbt_query_engine_type: str = Field(
        default="trino",
        description="Query engine adapter used by dbt profiles",
    )
    dbt_query_host: str = Field(
        default="trino",
        description="Query engine host for generated dbt profiles",
    )
    dbt_query_port: int = Field(
        default=8080,
        description="Query engine port for generated dbt profiles",
    )
    dbt_query_catalog: str = Field(
        default="iceberg",
        description="Base query engine catalog for generated dbt profiles",
    )
    dbt_query_schema: str = Field(
        default="raw",
        description="Default schema for generated dbt profiles",
    )
    dbt_query_user: str = Field(
        default="dagster",
        description="Query engine user for generated dbt profiles",
    )
    dbt_query_http_scheme: str = Field(
        default="http",
        description="HTTP scheme for generated dbt profiles",
    )
    dbt_query_auth_method: str = Field(
        default="none",
        description="Auth method for generated dbt profiles",
    )
    dbt_query_threads: int = Field(
        default=2,
        description="Worker threads for generated dbt profiles",
    )

    dbt_project_dir: str = Field(
        default="workflows/transforms/dbt",
        description="Path to dbt project directory",
    )
    dbt_manifest_path: str = Field(
        default="",
        description="Path to dbt manifest.json after running dbt docs generate",
    )
    dbt_catalog_path: str = Field(
        default="",
        description="Path to dbt catalog.json for column-level documentation",
    )

    def model_post_init(self, __context: object) -> None:
        """Populate derived dbt artifact paths after model initialization.

        Args:
            __context: Pydantic post-init context.

        """
        if not self.dbt_manifest_path:
            object.__setattr__(
                self, "dbt_manifest_path", f"{self.dbt_project_dir}/target/manifest.json"
            )
        if not self.dbt_catalog_path:
            object.__setattr__(
                self, "dbt_catalog_path", f"{self.dbt_project_dir}/target/catalog.json"
            )

    @computed_field
    @property
    def dbt_profiles_dir(self) -> str:
        """Return the dbt profiles directory path string.

        Returns:
            Profiles directory under the dbt project directory.

        """
        return f"{self.dbt_project_dir}/profiles"

    @property
    def dbt_project_path(self) -> Path:
        """Return the dbt project path as a ``Path``.

        Returns:
            Filesystem path to the dbt project root.

        """
        return Path(self.dbt_project_dir)

    @property
    def dbt_profiles_path(self) -> Path:
        """Return the dbt profiles path as a ``Path``.

        Returns:
            Filesystem path to the dbt profiles directory.

        """
        return Path(self.dbt_profiles_dir)


@lru_cache(maxsize=1)
def get_settings() -> DbtSettings:
    """Return cached dbt settings.

    Returns:
        Singleton dbt settings instance.

    """
    return DbtSettings()
