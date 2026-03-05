"""Dagster service plugin package."""

from phlo_dagster.dagster_ext import DagsterExtensionPlugin, IngestionEnginePlugin
from phlo_dagster.plugin import DagsterServicePlugin
from phlo_dagster.settings import DagsterSettings, get_settings

__all__ = [
    "DagsterServicePlugin",
    "DagsterExtensionPlugin",
    "IngestionEnginePlugin",
    "DagsterSettings",
    "get_settings",
]
__version__ = "0.1.2"
