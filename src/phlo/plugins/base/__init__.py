"""
Base classes for Phlo plugins.

These abstract base classes define the interfaces that plugins must implement.
"""

from __future__ import annotations

from phlo.plugins.base.catalog import CatalogPlugin
from phlo.plugins.base.cli import CliCommandPlugin
from phlo.plugins.base.governance import GovernancePlugin
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
    "CliCommandPlugin",
    "SourceConnectorPlugin",
    "QualityCheckPlugin",
    "TransformationPlugin",
    "ServicePlugin",
    "CatalogPlugin",
    "GovernancePlugin",
    "AssetProviderPlugin",
    "ResourceProviderPlugin",
    "OrchestratorAdapterPlugin",
]
