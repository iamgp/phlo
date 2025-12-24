# __init__.py - Phlo package initialization
"""
Phlo - Data Platform Framework

Declarative data pipelines with minimal boilerplate.

Usage::

    import phlo

    @phlo.quality(
        table="bronze.weather_observations",
        checks=[NullCheck(columns=["id"]), RangeCheck(column="temp", min_value=-50, max_value=60)],
    )
    def weather_quality():
        pass

    @phlo.ingestion(
        table_name="weather_observations",
        unique_key="id",
        group="weather",
    )
    def weather_ingestion(partition_date: str):
        return fetch_weather_data(partition_date)
"""

from __future__ import annotations

from phlo.quality.decorator import phlo_quality as quality

__version__ = "0.1.0-alpha.1"
__all__ = ["quality"]


def _resolve_export(export_name: str) -> object:
    from phlo.plugins.discovery import discover_plugins
    from phlo.plugins.registry import get_global_registry

    discover_plugins(plugin_type="dagster_extensions", auto_register=True)
    registry = get_global_registry()

    matches: list[object] = []
    for name in registry.list_dagster_extensions():
        plugin = registry.get_dagster_extension(name)
        if plugin is None:
            continue
        exports = plugin.get_exports()
        if export_name in exports:
            matches.append(exports[export_name])

    if not matches:
        raise AttributeError(
            f"phlo.{export_name} is not available. "
            "Install `phlo[defaults]` (or the relevant capability plugin) to enable it."
        )

    if len(matches) > 1:
        raise AttributeError(
            f"phlo.{export_name} is provided by multiple plugins. "
            "Uninstall the extras you don't want, or use the plugin package directly."
        )

    return matches[0]


def __getattr__(name: str) -> object:
    if name == "ingestion":
        return _resolve_export("ingestion")
    raise AttributeError(name)
