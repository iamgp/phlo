"""
User Workflow Discovery

This module discovers and loads workflow files from a user's project directory.
It dynamically imports Python modules which triggers decorator registration,
then collects all registered assets, jobs, and schedules.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import warnings
from pathlib import Path
from typing import Any

import dagster as dg

logger = logging.getLogger(__name__)

# Suppress Dagster preview warnings for stable API usage
warnings.filterwarnings(
    "ignore",
    message=".*is currently in preview.*",
    category=UserWarning,
)


def discover_user_workflows(
    workflows_path: Path | str,
    clear_registries: bool = False,
) -> dg.Definitions:
    """
    Discover and load user workflow files from a directory.

    This function scans the workflows directory for Python files, imports them
    (which triggers @phlo_ingestion and @phlo_quality decorator registration),
    and collects all registered Dagster assets and checks.

    Args:
        workflows_path: Path to workflows directory (e.g., "./workflows")
        clear_registries: Whether to clear asset registries before discovery
            (default: False). Set to True for testing.

    Returns:
        Dagster Definitions containing all discovered workflows

    Example:
        ```python
        # Discover workflows in ./workflows directory
        user_defs = discover_user_workflows(Path("./workflows"))

        # Merge with core definitions
        all_defs = Definitions.merge(core_defs, user_defs)
        ```

    Raises:
        FileNotFoundError: If workflows_path doesn't exist
        ImportError: If workflow modules fail to import
    """
    workflows_path = Path(workflows_path)

    if not workflows_path.exists():
        logger.warning(
            "Workflows directory not found: %s. No user workflows will be loaded.",
            workflows_path,
        )
        return dg.Definitions()

    if not workflows_path.is_dir():
        raise ValueError(f"Workflows path must be a directory, got: {workflows_path}")

    logger.info(f"Discovering user workflows in: {workflows_path}")

    # Optionally clear registries (useful for testing)
    if clear_registries:
        _clear_asset_registries()

    # Add parent directory to Python path so imports work
    parent_dir = workflows_path.parent.resolve()
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
        logger.debug(f"Added to Python path: {parent_dir}")

    # Import all workflow modules
    imported_modules = _import_workflow_modules(workflows_path)

    logger.info(f"Imported {len(imported_modules)} workflow modules from {workflows_path}")

    plugin_defs = _collect_dagster_extension_definitions()
    plugin_assets = list(plugin_defs.assets or [])
    plugin_asset_keys = {key for asset in plugin_assets for key in asset.keys}

    module_defs = (
        dg.load_definitions_from_modules(imported_modules) if imported_modules else dg.Definitions()
    )
    module_assets = list(module_defs.assets or [])
    filtered_assets = [
        asset for asset in module_assets if not asset.keys.issubset(plugin_asset_keys)
    ]

    if len(module_assets) != len(filtered_assets):
        logger.info(
            "Filtered %d duplicate assets from workflow modules",
            len(module_assets) - len(filtered_assets),
        )

    module_defs = dg.Definitions(
        assets=filtered_assets,
        asset_checks=module_defs.asset_checks,
        schedules=module_defs.schedules,
        sensors=module_defs.sensors,
        resources=module_defs.resources,
        jobs=module_defs.jobs,
    )

    merged = dg.Definitions.merge(plugin_defs, module_defs)
    logger.info("Discovered %d assets from Dagster plugins", len(plugin_assets))
    logger.info("Discovered %d assets from workflow modules", len(filtered_assets))
    return merged


def _import_workflow_modules(workflows_path: Path) -> list[Any]:
    """
    Import all Python modules in workflows directory.

    Args:
        workflows_path: Path to workflows directory

    Returns:
        List of imported module objects
    """
    imported_modules = []

    # Find all Python files
    py_files = list(workflows_path.rglob("*.py"))

    for py_file in py_files:
        # Skip __init__.py and files starting with underscore
        if py_file.name.startswith("_"):
            continue

        try:
            # Convert file path to module name
            # e.g., workflows/ingestion/weather/observations.py
            #    -> workflows.ingestion.weather.observations
            relative_path = py_file.relative_to(workflows_path.parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            logger.debug(f"Importing workflow module: {module_name}")

            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for: {py_file}")
                continue

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            imported_modules.append(module)
            logger.debug(f"Successfully imported: {module_name}")

        except Exception as exc:
            logger.error(
                f"Failed to import workflow module {py_file}: {exc}",
                exc_info=True,
            )
            # Continue with other modules rather than failing completely
            continue

    return imported_modules


def _collect_dagster_extension_definitions() -> dg.Definitions:
    from phlo.discovery import discover_plugins, get_global_registry

    discover_plugins(plugin_type="dagster_extensions", auto_register=True)
    registry = get_global_registry()

    definitions: list[dg.Definitions] = []
    for name in registry.list_dagster_extensions():
        plugin = registry.get_dagster_extension(name)
        if plugin is None:
            continue
        try:
            definitions.append(plugin.get_definitions())
        except Exception as exc:
            logger.error("Error creating Dagster definitions from plugin %s: %s", name, exc)

    return dg.Definitions.merge(*definitions) if definitions else dg.Definitions()


def _clear_asset_registries() -> None:
    """
    Clear all asset registries (for testing).

    This clears the global registries that decorators append to,
    allowing fresh discovery in test scenarios.
    """
    from phlo.discovery import discover_plugins, get_global_registry

    discover_plugins(plugin_type="dagster_extensions", auto_register=True)
    registry = get_global_registry()

    for name in registry.list_dagster_extensions():
        plugin = registry.get_dagster_extension(name)
        if plugin is None:
            continue
        try:
            plugin.clear_registries()
        except Exception as exc:
            logger.warning("Failed to clear registries for Dagster plugin %s: %s", name, exc)


def get_workflows_path_from_config() -> Path:
    """
    Get workflows path from configuration.

    Returns:
        Path to workflows directory from config, or default "workflows"

    Example:
        ```python
        workflows_path = get_workflows_path_from_config()
        defs = discover_user_workflows(workflows_path)
        ```
    """
    try:
        from phlo.config import get_settings

        settings = get_settings()

        # Check if workflows_path attribute exists
        if hasattr(settings, "workflows_path"):
            return Path(settings.workflows_path)

    except Exception as exc:
        logger.warning(f"Could not get workflows_path from config: {exc}")

    # Default fallback
    return Path("workflows")
