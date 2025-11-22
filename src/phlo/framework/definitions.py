"""
Framework Definitions

This module provides the main Dagster Definitions entry point for user projects.
It discovers user workflows and merges them with core Cascade framework resources.

This is the new entry point for user projects using Cascade as an installable package.
For the legacy in-package mode, use phlo.definitions instead.
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path

import dagster as dg

from phlo.config import get_settings
from phlo.framework.discovery import discover_user_workflows

logger = logging.getLogger(__name__)


def _default_executor() -> dg.ExecutorDefinition | None:
    """
    Choose an executor suited to the current environment.

    Multiprocessing is desirable on Linux servers, but DuckDB has been crashing
    (SIGBUS) when the container runs under Docker Desktop/Colima on macOS.
    Fall back to the in-process executor on macOS, and allow an override via
    CASCADE_FORCE_IN_PROCESS_EXECUTOR if someone hits the same issue elsewhere.

    Returns:
        Executor definition or None to use default
    """
    settings = get_settings()

    if settings.cascade_force_in_process_executor:
        return dg.in_process_executor

    if settings.cascade_force_multiprocess_executor:
        return dg.multiprocess_executor.configured({"max_concurrent": 4})

    if platform.system() == "Darwin":
        return dg.in_process_executor

    return dg.multiprocess_executor.configured({"max_concurrent": 4})


def build_core_resources() -> dg.Definitions:
    """
    Build core Cascade framework resources.

    Returns Definitions containing only resources (no assets).
    This allows user projects to use Cascade resources without
    loading all the example assets.

    Returns:
        Definitions with core resources
    """
    try:
        from phlo.defs.resources import build_defs as build_resource_defs

        return build_resource_defs()
    except ImportError as exc:
        logger.warning(f"Could not import phlo.defs.resources: {exc}")
        return dg.Definitions()


def build_definitions(
    workflows_path: Path | str | None = None,
    include_core_assets: bool = False,
) -> dg.Definitions:
    """
    Build Dagster definitions by merging user workflows with framework resources.

    This is the main entry point for user projects. It:
    1. Loads configuration
    2. Discovers user workflows from workflows_path
    3. Loads core Cascade resources
    4. Optionally loads core Cascade assets (examples)
    5. Merges everything together

    Args:
        workflows_path: Path to user workflows directory. If None, uses
            configuration value (default: "workflows")
        include_core_assets: Whether to include core Cascade example assets
            (default: False). Set to True for development/testing.

    Returns:
        Merged Dagster Definitions

    Example:
        ```python
        # In your project's workspace.yaml:
        # load_from:
        #   - python_module:
        #       module_name: phlo.framework.definitions

        # Basic usage (loads workflows from ./workflows)
        defs = build_definitions()

        # Custom workflows path
        defs = build_definitions(workflows_path="custom_workflows")

        # Include core examples for reference
        defs = build_definitions(include_core_assets=True)
        ```
    """
    settings = get_settings()

    # Determine workflows path
    if workflows_path is None:
        workflows_path = Path(settings.workflows_path)
    else:
        workflows_path = Path(workflows_path)

    logger.info(f"Building Cascade definitions with workflows from: {workflows_path}")

    # Discover user workflows
    try:
        user_defs = discover_user_workflows(workflows_path)
        user_assets = list(user_defs.assets or [])
        user_checks = list(user_defs.asset_checks or [])
        logger.info(
            "Discovered %d user assets, %d checks", len(user_assets), len(user_checks)
        )
    except Exception as exc:
        logger.error(f"Failed to discover user workflows: {exc}", exc_info=True)
        user_defs = dg.Definitions()

    # Build core resources
    core_resources = build_core_resources()

    # Optionally include core assets (examples)
    definitions_to_merge = [core_resources, user_defs]

    if include_core_assets:
        logger.info("Including core Cascade example assets")
        try:
            from phlo.definitions import defs as core_defs

            definitions_to_merge.append(core_defs)
        except ImportError as exc:
            logger.warning(f"Could not import core definitions: {exc}")

    # Merge all definitions
    merged = dg.Definitions.merge(*definitions_to_merge)

    # Configure executor
    executor = _default_executor()

    # Build final definitions - use explicit parameters instead of unpacking
    final_defs = dg.Definitions(
        assets=merged.assets,
        asset_checks=merged.asset_checks,
        schedules=merged.schedules,
        sensors=merged.sensors,
        resources=merged.resources,
        jobs=merged.jobs,
        executor=executor,
    )

    final_assets = list(final_defs.assets or [])
    final_checks = list(final_defs.asset_checks or [])
    final_jobs = list(final_defs.jobs or [])
    final_schedules = list(final_defs.schedules or [])
    logger.info(
        "Built Cascade definitions: %d assets, %d checks, %d jobs, %d schedules",
        len(final_assets),
        len(final_checks),
        len(final_jobs),
        len(final_schedules),
    )

    return final_defs


# Environment variable to control whether to include core assets
_INCLUDE_CORE_ASSETS = os.environ.get(
    "CASCADE_INCLUDE_CORE_ASSETS", "false"
).lower() in (
    "true",
    "1",
    "yes",
)

# Global definitions instance for Dagster to load
# This is what gets imported by workspace.yaml
defs = build_definitions(include_core_assets=_INCLUDE_CORE_ASSETS)
