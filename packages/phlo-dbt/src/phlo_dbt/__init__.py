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
from phlo_dbt.helpers import (
    DbtManifestTable,
    build_partition_vars,
    ensure_compiled,
    extract_manifest_tables,
    normalize_selectors,
    select_manifest_models,
)
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
    "DbtManifestTable",
    "build_partition_vars",
    "build_dbt_asset_specs",
    "ensure_compiled",
    "ensure_dbt_profile",
    "extract_manifest_tables",
    "get_settings",
    "normalize_selectors",
    "render_dbt_profile_yaml",
    "resolve_dbt_target_name",
    "resolve_dbt_runtime_config",
    "select_manifest_models",
    "write_dbt_profile",
    "write_dbt_scaffold",
]
