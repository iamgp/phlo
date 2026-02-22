"""Constants for plugin registry type configuration."""

from __future__ import annotations

TYPE_CONFIG = {
    "source_connectors": ("_sources", "source", "Source connector"),
    "quality_checks": ("_quality_checks", "quality", "Quality check"),
    "transformations": ("_transformations", "transformation", "Transformation"),
    "services": ("_services", "service", "Service"),
    "cli_commands": ("_cli_commands", "cli", "CLI command"),
    "hooks": ("_hooks", "hooks", "Hook"),
    "asset_providers": ("_assets", "assets", "Asset provider"),
    "resource_providers": ("_resources", "resources", "Resource provider"),
    "orchestrators": ("_orchestrators", "orchestrators", "Orchestrator"),
    "catalogs": ("_catalogs", "catalogs", "Catalog"),
}
