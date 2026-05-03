"""Shared utilities for plugin commands."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys

from packaging.version import parse
from rich.console import Console
from rich.table import Table

from phlo.capabilities import missing_required_capabilities
from phlo.capabilities.support import coerce_capability_support
from phlo.cli.commands.plugin.scaffold import create_plugin_package  # noqa: F401
from phlo.logging import get_logger
from phlo.plugins import get_plugin_info
from phlo.plugins.base import PluginMetadata
from phlo.plugins.discovery import get_global_registry, get_service

console = Console()
logger = get_logger(__name__)

PLUGIN_TYPE_MAP = {
    "sources": "source_connectors",
    "quality": "quality_checks",
    "transforms": "transformations",
    "services": "services",
    "hooks": "hooks",
    "assets": "asset_providers",
    "resources": "resource_providers",
    "orchestrators": "orchestrators",
    "catalogs": "catalogs",
}

PLUGIN_TYPE_CHOICES = [
    "sources",
    "quality",
    "transforms",
    "services",
    "hooks",
    "assets",
    "resources",
    "orchestrators",
    "catalogs",
]

INTERNAL_TO_REGISTRY_TYPE = {
    "source_connectors": "source",
    "quality_checks": "quality",
    "transformations": "transform",
    "services": "service",
    "hooks": "hooks",
    "asset_providers": "assets",
    "resource_providers": "resources",
    "orchestrators": "orchestrators",
    "catalogs": "catalogs",
}

SCAFFOLD_TYPE_MAP = {
    "sources": "source",
    "source": "source",
    "quality": "quality",
    "transforms": "transform",
    "transform": "transform",
    "services": "service",
    "service": "service",
    "hooks": "hook",
    "catalogs": "catalog",
    "assets": "asset",
    "resources": "resource",
    "orchestrators": "orchestrator",
}


def run_pip(args: list[str], *, timeout: float = 300) -> None:
    """Install packages using pip, with uv fallback for uv-managed environments."""
    operation = args[0] if args else "unknown"
    if importlib.util.find_spec("pip") is not None:
        command = [sys.executable, "-m", "pip", *args]
        installer = "pip"
    else:
        if shutil.which("uv") is None:
            raise RuntimeError(
                "pip module is unavailable and 'uv' is not installed; cannot install packages."
            )
        command = ["uv", "pip", *args]
        installer = "uv"

    try:
        logger.info("plugin_pip_command_started", operation=operation, installer=installer)
        subprocess.run(command, check=True, timeout=timeout)
        logger.info("plugin_pip_command_succeeded", operation=operation, installer=installer)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "plugin_pip_command_failed",
            operation=operation,
            installer=installer,
            return_code=exc.returncode,
        )
        raise
    except subprocess.TimeoutExpired as exc:
        message = f"Install command timed out after {timeout}s: {' '.join(command)}"
        logger.error(
            "plugin_pip_command_timed_out",
            operation=operation,
            installer=installer,
            timeout_seconds=timeout,
        )
        raise RuntimeError(message) from exc


def registry_plugin_to_dict(plugin) -> dict:
    """Convert registry plugin to dictionary."""
    return {
        "name": plugin.name,
        "type": plugin.type,
        "package": plugin.package,
        "version": plugin.version,
        "description": plugin.description,
        "author": plugin.author,
        "homepage": plugin.homepage,
        "tags": plugin.tags,
        "verified": plugin.verified,
        "core": plugin.core,
    }


def collect_installed_plugins(plugin_type: str) -> list[dict]:
    """Collect installed plugins of given type."""
    registry = get_global_registry()
    installed: list[dict] = []

    def add_plugin(plugin_key: str, name: str) -> None:
        """Append discovered plugin metadata for one registry entry."""
        info = get_plugin_info(plugin_key, name)
        if not info:
            return
        required_capabilities = info.get("requires_capabilities", [])
        optional_capabilities = info.get("optional_capabilities", [])
        support = coerce_capability_support(info.get("support"))
        missing_capabilities = missing_required_capabilities(
            PluginMetadata(
                name=info["name"],
                version=info["version"],
                requires_capabilities=list(required_capabilities),
                optional_capabilities=list(optional_capabilities),
                support=support,
            )
        )
        installed.append(
            {
                "name": info["name"],
                "type": INTERNAL_TO_REGISTRY_TYPE.get(plugin_key, plugin_key),
                "version": info["version"],
                "description": info.get("description", ""),
                "author": info.get("author", ""),
                "homepage": info.get("homepage", ""),
                "tags": info.get("tags", []),
                "installed": True,
                "required_capabilities": required_capabilities,
                "optional_capabilities": optional_capabilities,
                "support": support.to_dict(),
                "missing_capabilities": missing_capabilities,
                "ready": len(missing_capabilities) == 0,
            }
        )

    for type_key, names in registry.list_all_plugins().items():
        if plugin_type != "all" and PLUGIN_TYPE_MAP.get(plugin_type) != type_key:
            continue
        if type_key == "services":
            for name in names:
                service = get_service(name)
                if not service:
                    continue
                metadata = service.metadata
                missing_capabilities = missing_required_capabilities(metadata)
                installed.append(
                    {
                        "name": metadata.name,
                        "type": "service",
                        "version": metadata.version,
                        "description": metadata.description,
                        "author": metadata.author,
                        "homepage": metadata.homepage,
                        "tags": metadata.tags,
                        "installed": True,
                        "category": service.category,
                        "profile": service.profile,
                        "default": service.is_default,
                        "required_capabilities": metadata.requires_capabilities,
                        "optional_capabilities": metadata.optional_capabilities,
                        "support": metadata.support.to_dict(),
                        "missing_capabilities": missing_capabilities,
                        "ready": len(missing_capabilities) == 0,
                    }
                )
            continue

        for name in names:
            add_plugin(type_key, name)

    return installed


def collect_registry_plugins(plugin_type: str) -> list[dict]:
    """Collect registry plugins of given type."""
    from phlo.plugins.registry_client import list_registry_plugins

    registry_plugins = list_registry_plugins()
    if plugin_type != "all":
        # Translate CLI type to internal type first, then to registry type
        internal_type = PLUGIN_TYPE_MAP.get(plugin_type, plugin_type)
        registry_type = INTERNAL_TO_REGISTRY_TYPE.get(internal_type)
        registry_plugins = [plugin for plugin in registry_plugins if plugin.type == registry_type]
    return [registry_plugin_to_dict(plugin) for plugin in registry_plugins]


def render_plugin_table(title: str, plugins: list[dict]) -> None:
    """Render a table of plugins."""
    console.print(f"\n{title}:")
    if not plugins:
        console.print("  (none)")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Author", style="white")
    table.add_column("Ready", style="magenta")

    for plugin in plugins:
        ready = plugin.get("ready")
        ready_label = "yes" if ready is True else ("no" if ready is False else "n/a")
        missing = plugin.get("missing_capabilities") or []
        if ready is False and missing:
            ready_label = f"no ({', '.join(missing)})"
        table.add_row(
            plugin["name"],
            plugin["type"],
            plugin["version"],
            plugin.get("author", "unknown") or "unknown",
            ready_label,
        )

    console.print(table)


def get_installed_version(package: str) -> str | None:
    """Get installed version of a package."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def version_tuple(version: str) -> tuple[int, object]:
    """Convert version string to tuple for comparison."""
    try:
        return (0, parse(version))
    except Exception:
        return (0, parse("0"))


def is_version_newer(installed: str, available: str) -> bool:
    """Check if available version is newer than installed."""
    try:
        return parse(available) > parse(installed)
    except Exception:
        return available != installed


def find_available_updates(registry_plugins) -> list[dict]:
    """Find available updates for installed plugins."""
    updates = []
    for plugin in registry_plugins:
        installed_version = get_installed_version(plugin.package)
        if not installed_version:
            continue
        if is_version_newer(installed_version, plugin.version):
            updates.append(
                {
                    "name": plugin.name,
                    "package": plugin.package,
                    "installed_version": installed_version,
                    "available_version": plugin.version,
                }
            )
    return updates
