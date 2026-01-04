"""
User Workflow Discovery

This module discovers and loads workflow files from a user's project directory.
It dynamically imports Python modules which triggers capability registration,
then delegates to the active orchestrator adapter.
"""

from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path
from typing import Any

from phlo.capabilities.discovery import discover_capabilities
from phlo.capabilities.registry import clear_capabilities, get_capability_registry
from phlo.logging import get_logger
from phlo.orchestrators import get_active_orchestrator

logger = get_logger(__name__)

# Suppress preview warnings from orchestrators that emit them on import.
warnings.filterwarnings("ignore", message=".*is currently in preview.*", category=UserWarning)


def discover_user_workflows(
    workflows_path: Path | str,
    clear_registries: bool = False,
) -> Any:
    """
    Discover and load user workflow files from a directory.

    Imports workflow modules (which registers capability specs) and builds
    orchestrator definitions using the active adapter.
    """
    workflows_path = Path(workflows_path)

    if clear_registries:
        _clear_capability_registries()

    if not workflows_path.exists():
        logger.warning(
            "Workflows directory not found: %s. No user workflows will be loaded.",
            workflows_path,
        )
        imported_modules: list[Any] = []
    elif not workflows_path.is_dir():
        raise ValueError(f"Workflows path must be a directory, got: {workflows_path}")
    else:
        logger.info(f"Discovering user workflows in: {workflows_path}")
        parent_dir = workflows_path.parent.resolve()
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
            logger.debug(f"Added to Python path: {parent_dir}")
        imported_modules = _import_workflow_modules(workflows_path)
        logger.info(f"Imported {len(imported_modules)} workflow modules from {workflows_path}")

    # Discover provider plugins after modules are imported.
    discover_capabilities()

    registry = get_capability_registry()
    adapter = get_active_orchestrator()
    return adapter.build_definitions(
        assets=registry.list_assets(),
        checks=registry.list_checks(),
        resources=registry.list_resources(),
    )


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


def _collect_dagster_extension_definitions() -> Any:
    from phlo.discovery import discover_plugins, get_global_registry

    try:
        import dagster as dg
    except Exception:  # noqa: BLE001 - optional dependency
        return None

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


def _ensure_core_resources(definitions: Any) -> Any:
    try:
        import dagster as dg
    except Exception:  # noqa: BLE001 - optional dependency
        return definitions

    resources = dict(definitions.resources or {})
    if "trino" not in resources:
        trino_resource = _default_trino_resource()
        if trino_resource is not None:
            resources["trino"] = trino_resource
    if resources == (definitions.resources or {}):
        return definitions
    return dg.Definitions.merge(definitions, dg.Definitions(resources=resources))


def _default_trino_resource() -> Any | None:
    try:
        from phlo_trino.resource import TrinoResource
    except Exception:  # noqa: BLE001 - optional dependency
        return None
    return TrinoResource()


def _clear_capability_registries() -> None:
    """Clear capability registries (for testing)."""
    from phlo.discovery import discover_plugins, get_global_registry

    clear_capabilities()
    discover_plugins(plugin_type="asset_providers", auto_register=True)
    discover_plugins(plugin_type="dagster_extensions", auto_register=True)
    registry = get_global_registry()

    for name in registry.list_asset_providers():
        plugin = registry.get_asset_provider(name)
        if plugin is None:
            continue
        clear_fn = getattr(plugin, "clear_registries", None)
        if callable(clear_fn):
            try:
                clear_fn()
            except Exception as exc:
                logger.warning("Failed to clear registries for asset provider %s: %s", name, exc)

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
