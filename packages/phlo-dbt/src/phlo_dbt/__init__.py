"""Phlo dbt integration package.

This package provides dbt integration for the Phlo data platform, including:
- Asset specification generation from dbt manifests
- Runtime configuration management for dbt profiles
- Project scaffolding utilities
- CLI commands for dbt operations

Example:
    >>> from phlo_dbt import build_dbt_asset_specs, DbtRuntimeConfig
    >>> specs = build_dbt_asset_specs()
    >>> config = DbtRuntimeConfig(target_name="prod")

"""

from phlo_dbt.assets import build_dbt_asset_specs
from phlo_dbt.runtime_config import (
    DEFAULT_DBT_TARGET,
    DbtRuntimeConfig,
    ensure_dbt_profile,
    render_dbt_profile_yaml,
    resolve_dbt_target_name,
    resolve_dbt_runtime_config,
    write_dbt_profile,
)
from phlo_dbt.scaffold import write_dbt_scaffold
from phlo_dbt.settings import DbtSettings, get_settings

__all__ = [
    "DEFAULT_DBT_TARGET",
    "DbtRuntimeConfig",
    "DbtSettings",
    "build_dbt_asset_specs",
    "ensure_dbt_profile",
    "get_settings",
    "render_dbt_profile_yaml",
    "resolve_dbt_target_name",
    "resolve_dbt_runtime_config",
    "write_dbt_profile",
    "write_dbt_scaffold",
]
