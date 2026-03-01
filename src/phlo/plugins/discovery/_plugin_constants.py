"""Shared constants for plugin discovery and registration."""

from __future__ import annotations

from phlo.plugins.base import (
    AssetProviderPlugin,
    CatalogPlugin,
    CliCommandPlugin,
    OrchestratorAdapterPlugin,
    Plugin,
    QualityCheckPlugin,
    QualityProviderPlugin,
    ResourceProviderPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.hooks import HookPlugin

NO_AUTO_DISCOVER_ENV = "PHLO_NO_AUTO_DISCOVER"
TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
FALSY_ENV_VALUES = frozenset({"0", "false", "no", "off", ""})

# Entry point group names for different plugin types.
ENTRY_POINT_GROUPS = {
    "source_connectors": "phlo.plugins.sources",
    "quality_checks": "phlo.plugins.quality",
    "quality_providers": "phlo.plugins.quality_providers",
    "transformations": "phlo.plugins.transforms",
    "services": "phlo.plugins.services",
    "cli_commands": "phlo.plugins.cli",
    "hooks": "phlo.plugins.hooks",
    "catalogs": "phlo.plugins.catalogs",
    "asset_providers": "phlo.plugins.assets",
    "resource_providers": "phlo.plugins.resources",
    "orchestrators": "phlo.plugins.orchestrators",
}

# Maps plugin type to registry registration method name.
PLUGIN_REGISTER_METHODS = {
    "source_connectors": "register_source_connector",
    "quality_checks": "register_quality_check",
    "quality_providers": "register_quality_provider",
    "transformations": "register_transformation",
    "services": "register_service",
    "cli_commands": "register_cli_command_plugin",
    "hooks": "register_hook_plugin",
    "catalogs": "register_catalog",
    "asset_providers": "register_asset_provider",
    "resource_providers": "register_resource_provider",
    "orchestrators": "register_orchestrator",
}

# Maps plugin type to registry getter method name.
PLUGIN_GETTER_METHODS = {
    "source_connectors": "get_source_connector",
    "quality_checks": "get_quality_check",
    "quality_providers": "get_quality_provider",
    "transformations": "get_transformation",
    "services": "get_service",
    "cli_commands": "get_cli_command_plugin",
    "hooks": "get_hook_plugin",
    "catalogs": "get_catalog",
    "asset_providers": "get_asset_provider",
    "resource_providers": "get_resource_provider",
    "orchestrators": "get_orchestrator",
}

PLUGIN_EXPECTED_TYPES: dict[str, type[Plugin]] = {
    "source_connectors": SourceConnectorPlugin,
    "quality_checks": QualityCheckPlugin,
    "quality_providers": QualityProviderPlugin,
    "transformations": TransformationPlugin,
    "services": ServicePlugin,
    "cli_commands": CliCommandPlugin,
    "hooks": HookPlugin,
    "catalogs": CatalogPlugin,
    "asset_providers": AssetProviderPlugin,
    "resource_providers": ResourceProviderPlugin,
    "orchestrators": OrchestratorAdapterPlugin,
}
