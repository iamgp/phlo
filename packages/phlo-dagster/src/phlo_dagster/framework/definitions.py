"""Framework definitions builder for Phlo-Dagster projects.

This module provides the primary entry point for building Dagster Definitions
in Phlo projects. It orchestrates the discovery of user workflows, merges them
with framework-provided resources, and configures executor and sensor settings.

Building Process:
    1. Setup logging and load configuration
    2. Discover user workflows from configured path
    3. Optionally refresh schema contracts
    4. Collect Dagster extension definitions from plugins
    5. Collect WAP (Write-Audit-Publish) definitions if catalog supports refs
    6. Merge all definition sources
    7. Ensure core resources (Trino, etc.)
    8. Select appropriate executor based on platform
    9. Return final Definitions object

Integration Points:
    - User workflows: Imported from workflows/ directory
    - Extensions: Discovered via phlo.plugins.dagster entry_points
    - WAP sensors: Optional, requires VersionedCatalog capability
    - Core resources: Trino connection, logging, etc.

Executor Selection:
    Platform-aware selection with priority:
    1. PHLO_FORCE_IN_PROCESS_EXECUTOR (override)
    2. PHLO_FORCE_MULTIPROCESS_EXECUTOR (override)
    3. PHLO_HOST_PLATFORM detection
    4. platform.system() fallback

    Darwin/macOS defaults to in-process for Docker Desktop compatibility.

Entry Points:
    - build_definitions(): Programmatic entry point
    - defs: Global Definitions instance for Dagster to load

    Configured in workspace.yaml::

        load_from:
          - python_module:
              module_name: phlo_dagster.framework.definitions

Example:
    Basic usage::

        from phlo_dagster.framework.definitions import build_definitions

        defs = build_definitions()

    Custom workflows path::

        defs = build_definitions(workflows_path="custom_workflows")

"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

import dagster as dg

from phlo.capabilities.interfaces import VersionedCatalog
from phlo.capabilities.resolver import resolve_capability
from phlo.exceptions import PhloCapabilitySetupError
from phlo_dagster.framework.discovery import (
    _collect_dagster_extension_definitions,
    _ensure_core_resources,
    discover_user_workflows,
)
from phlo_dagster.framework.schema_contracts import maybe_refresh_contracts
from phlo_dagster.settings import get_settings
from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _collect_wap_definitions() -> dg.Definitions | None:
    """Load WAP sensors when a versioned catalog capability is available.

    Args:
        None

    Returns:
        Dagster Definitions containing WAP sensors, or None if WAP is not available.

    Raises:
        No explicit exceptions raised. Logs warnings for incompatible providers.

    """
    if os.getenv("PHLO_DAGSTER_DEV") == "1" and os.getenv("PHLO_WAP_SENSORS_ENABLED") is None:
        logger.info("dagster_wap_definitions_skipped_in_local_dev")
        return None

    resolution = resolve_capability("catalog")
    if resolution is None:
        return None

    if not (resolution.support.supports_refs and resolution.support.supports_promote):
        return None

    provider = resolution.provider
    if not isinstance(provider, VersionedCatalog):
        logger.warning(
            "dagster_wap_catalog_provider_incompatible",
            capability_name=resolution.name,
            provider_type=type(provider).__name__,
        )
        return None

    try:
        from phlo_dagster.wap_sensors import get_wap_definitions
    except Exception:
        logger.warning(
            "dagster_wap_definitions_unavailable",
            capability_name=resolution.name,
            exc_info=True,
        )
        return None

    logger.info(
        "dagster_wap_definitions_enabled",
        capability_name=resolution.name,
    )
    return get_wap_definitions()


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
        logger.debug("phlo_host_platform_detected", host_platform=host_platform)
    else:
        logger.info("using_phlo_host_platform", host_platform=host_platform)

    # Use in-process executor if host is macOS
    if host_platform == "Darwin":
        logger.info("Using in-process executor (host platform: Darwin/macOS)")
        return dg.in_process_executor

    # Default: multiprocess executor for Linux
    logger.info("using_multiprocess_executor", host_platform=host_platform)
    return dg.multiprocess_executor.configured({"max_concurrent": 4})


def build_definitions(
    workflows_path: Path | str | None = None,
) -> Any:
    """
    Build Dagster definitions by merging user workflows with framework resources.

    This is the main entry point for user projects. It:
    1. Loads configuration
    2. Discovers user workflows from workflows_path
    3. Loads core Phlo resources
    4. Merges everything together

    Args:
        workflows_path: Path to user workflows directory. If None, uses
            configuration value (default: "workflows")
    Returns:
        Merged Dagster Definitions

    Example:
        ```python
        # In your project's workspace.yaml:
        # load_from:
        #   - python_module:
        #       module_name: phlo_dagster.framework.definitions

        # Basic usage (loads workflows from ./workflows)
        defs = build_definitions()

        # Custom workflows path
        defs = build_definitions(workflows_path="custom_workflows")

        defs = build_definitions()
        ```

    """
    setup_logging()
    settings = get_settings()

    # Determine workflows path
    if workflows_path is None:
        workflows_path = Path(settings.workflows_path)
    else:
        workflows_path = Path(workflows_path)

    logger.info("building_phlo_definitions", workflows_path=str(workflows_path))

    # Discover user workflows
    try:
        user_defs = discover_user_workflows(workflows_path, clear_registries=True)
        maybe_refresh_contracts(workflows_path, logger)
        user_assets = list(getattr(user_defs, "assets", []) or [])
        user_checks = list(getattr(user_defs, "asset_checks", []) or [])
        logger.info("Discovered %d user assets, %d checks", len(user_assets), len(user_checks))
    except PhloCapabilitySetupError as exc:
        if exc.required:
            logger.error(
                "required_capability_setup_failed",
                capability=exc.capability,
                error=str(exc),
                workflows_path=str(workflows_path),
                exc_info=True,
            )
            raise
        logger.warning(
            "optional_capability_degraded",
            capability=exc.capability,
            error=str(exc),
            workflows_path=str(workflows_path),
        )
        user_defs = dg.Definitions()
    except Exception as exc:
        logger.error(
            "failed_to_discover_user_workflows",
            workflows_path=str(workflows_path),
            error=str(exc),
            exc_info=True,
        )
        user_defs = dg.Definitions()

    dagster_defs = _collect_dagster_extension_definitions()
    definitions_to_merge = [user_defs]
    if dagster_defs is not None:
        definitions_to_merge.append(dagster_defs)
    wap_defs = _collect_wap_definitions()
    if wap_defs is not None:
        definitions_to_merge.append(wap_defs)

    merged = dg.Definitions.merge(*definitions_to_merge)
    merged = _ensure_core_resources(merged)

    executor = _default_executor()
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


# Global definitions instance for Dagster to load.
defs = build_definitions()
