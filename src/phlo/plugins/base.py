"""
Base classes for Phlo plugins.

These abstract base classes define the interfaces that plugins must implement.

This module is a compatibility shim that re-exports from the new modular structure.
All imports from `phlo.plugins.base` continue to work as before.
"""

from __future__ import annotations

from phlo.plugins.base.catalog import CatalogPlugin, TrinoCatalogPlugin
from phlo.plugins.base.cli import CliCommandPlugin
from phlo.plugins.base.dagster_ext import DagsterExtensionPlugin, IngestionEnginePlugin
from phlo.plugins.base.observatory_ext import ObservatoryExtensionPlugin
from phlo.plugins.base.orchestrator import OrchestratorAdapterPlugin
from phlo.plugins.base.plugin import Plugin, PluginMetadata
from phlo.plugins.base.providers import AssetProviderPlugin, ResourceProviderPlugin
from phlo.plugins.base.quality import QualityCheckPlugin
from phlo.plugins.base.service import ServicePlugin
from phlo.plugins.base.source import SourceConnectorPlugin
from phlo.plugins.base.transform import TransformationPlugin

__all__ = [
    "Plugin",
    "PluginMetadata",
    "DagsterExtensionPlugin",
    "IngestionEnginePlugin",
    "ObservatoryExtensionPlugin",
    "CliCommandPlugin",
    "SourceConnectorPlugin",
    "QualityCheckPlugin",
    "TransformationPlugin",
    "ServicePlugin",
    "CatalogPlugin",
    "TrinoCatalogPlugin",
    "AssetProviderPlugin",
    "ResourceProviderPlugin",
    "OrchestratorAdapterPlugin",
]
