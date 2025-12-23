"""
Framework Definitions

This module provides the main Dagster Definitions entry point for user projects.
It discovers user workflows and merges them with core Phlo framework resources.

This is the new entry point for user projects using Phlo as an installable package.
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

    Priority order:
    1. PHLO_FORCE_IN_PROCESS_EXECUTOR (explicit override)
    2. PHLO_FORCE_MULTIPROCESS_EXECUTOR (explicit override)
    3. PHLO_HOST_PLATFORM (from environment, for Docker on macOS)
    4. platform.system() (fallback for local dev)

    Multiprocessing is desirable on Linux servers, but DuckDB has been crashing
    (SIGBUS) when the container runs under Docker Desktop/Colima on macOS.
    Fall back to the in-process executor on macOS, and allow overrides if needed.

    Returns:
        Executor definition or None to use default
    """
    settings = get_settings()

    # Priority 1: Explicit force in-process
    if settings.phlo_force_in_process_executor:
        logger.info("Using in-process executor (forced via PHLO_FORCE_IN_PROCESS_EXECUTOR)")
        return dg.in_process_executor

    # Priority 2: Explicit force multiprocess
    if settings.phlo_force_multiprocess_executor:
        logger.info("Using multiprocess executor (forced via PHLO_FORCE_MULTIPROCESS_EXECUTOR)")
        return dg.multiprocess_executor.configured({"max_concurrent": 4})

    # Priority 3: Check host platform (for Docker on macOS detection)
    host_platform = settings.phlo_host_platform
    if host_platform is None:
        # Priority 4: Fall back to container/local platform
        host_platform = platform.system()
        logger.debug(f"PHLO_HOST_PLATFORM not set, detected: {host_platform}")
    else:
        logger.info(f"Using PHLO_HOST_PLATFORM: {host_platform}")

    # Use in-process executor if host is macOS
    if host_platform == "Darwin":
        logger.info("Using in-process executor (host platform: Darwin/macOS)")
        return dg.in_process_executor

    # Default: multiprocess executor for Linux
    logger.info(f"Using multiprocess executor (host platform: {host_platform})")
    return dg.multiprocess_executor.configured({"max_concurrent": 4})


def build_definitions(
    workflows_path: Path | str | None = None,
    include_core_assets: bool = False,
) -> dg.Definitions:
    """
    Build Dagster definitions by merging user workflows with framework resources.

    This is the main entry point for user projects. It:
    1. Loads configuration
    2. Discovers user workflows from workflows_path
    3. Loads core Phlo resources
    4. Optionally loads core Phlo assets (examples)
    5. Merges everything together

    Args:
        workflows_path: Path to user workflows directory. If None, uses
            configuration value (default: "workflows")
        include_core_assets: Whether to include core Phlo example assets
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

    logger.info(f"Building Phlo definitions with workflows from: {workflows_path}")

    # Discover user workflows
    try:
        user_defs = discover_user_workflows(workflows_path, clear_registries=True)
        user_assets = list(user_defs.assets or [])
        user_checks = list(user_defs.asset_checks or [])
        logger.info("Discovered %d user assets, %d checks", len(user_assets), len(user_checks))
    except Exception as exc:
        logger.error(f"Failed to discover user workflows: {exc}", exc_info=True)
        user_defs = dg.Definitions()

    # Definitions provided by installed Dagster extension plugins (and user modules)
    definitions_to_merge = [user_defs]

    if include_core_assets:
        logger.info("Including core Phlo example assets")
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
        "Built Phlo definitions: %d assets, %d checks, %d jobs, %d schedules",
        len(final_assets),
        len(final_checks),
        len(final_jobs),
        len(final_schedules),
    )

    return final_defs


# Environment variable to control whether to include core assets
_INCLUDE_CORE_ASSETS = os.environ.get("PHLO_INCLUDE_CORE_ASSETS", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Global definitions instance for Dagster to load
# This is what gets imported by workspace.yaml
defs = build_definitions(include_core_assets=_INCLUDE_CORE_ASSETS)
