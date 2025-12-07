# definitions.py - Main entry point for Dagster definitions in the Cascade lakehouse platform
# This module aggregates all Dagster components (assets, jobs, schedules, sensors, resources, checks)
# from various submodules and configures the executor based on the environment.

from __future__ import annotations

import logging
import platform

import dagster as dg

from phlo.config import config
from phlo.defs.nessie import build_defs as build_nessie_defs
from phlo.defs.publishing import build_defs as build_publishing_defs
from phlo.defs.resources import build_defs as build_resource_defs
from phlo.defs.schedules import build_defs as build_schedule_defs
from phlo.defs.sensors import build_defs as build_sensor_defs
from phlo.defs.transform import build_defs as build_transform_defs
from phlo.defs.validation import build_defs as build_validation_defs
from phlo.ingestion import get_ingestion_assets
from phlo.quality import get_quality_checks

logger = logging.getLogger(__name__)


# Executor selection function: Chooses between in-process and multiprocess executors
# based on platform and configuration to handle multiprocessing issues on macOS
def _default_executor() -> dg.ExecutorDefinition | None:
    """
    Choose an executor suited to the current environment.

    Priority order:
    1. CASCADE_FORCE_IN_PROCESS_EXECUTOR (explicit override)
    2. CASCADE_FORCE_MULTIPROCESS_EXECUTOR (explicit override)
    3. CASCADE_HOST_PLATFORM (from environment, for Docker on macOS)
    4. platform.system() (fallback for local dev)

    Multiprocessing is desirable on Linux servers, but DuckDB has been crashing (SIGBUS) when the
    container runs under Docker Desktop/Colima on macOS. Fall back to the in-process executor on
    macOS, and allow overrides if needed.
    """
    # Priority 1: Explicit force in-process
    if config.cascade_force_in_process_executor:
        logger.info("Using in-process executor (forced via CASCADE_FORCE_IN_PROCESS_EXECUTOR)")
        return dg.in_process_executor

    # Priority 2: Explicit force multiprocess
    if config.cascade_force_multiprocess_executor:
        logger.info("Using multiprocess executor (forced via CASCADE_FORCE_MULTIPROCESS_EXECUTOR)")
        return dg.multiprocess_executor.configured({"max_concurrent": 4})

    # Priority 3: Check host platform (for Docker on macOS detection)
    host_platform = config.cascade_host_platform
    if host_platform is None:
        # Priority 4: Fall back to container/local platform
        host_platform = platform.system()
        logger.debug(f"CASCADE_HOST_PLATFORM not set, detected: {host_platform}")
    else:
        logger.info(f"Using CASCADE_HOST_PLATFORM: {host_platform}")

    # Use in-process executor if host is macOS
    if host_platform == "Darwin":
        logger.info("Using in-process executor (host platform: Darwin/macOS)")
        return dg.in_process_executor

    # Default: multiprocess executor for Linux
    logger.info(f"Using multiprocess executor (host platform: {host_platform})")
    return dg.multiprocess_executor.configured({"max_concurrent": 4})


# Merge definitions function: Combines all Dagster components from submodules
# into a single Definitions object with the selected executor
def _merged_definitions() -> dg.Definitions:
    # Get user-defined ingestion assets and quality checks
    ingestion_defs = dg.Definitions(assets=get_ingestion_assets())
    quality_defs = dg.Definitions(asset_checks=get_quality_checks())

    merged = dg.Definitions.merge(
        build_resource_defs(),
        ingestion_defs,
        build_transform_defs(),
        build_publishing_defs(),
        quality_defs,
        build_nessie_defs(),
        build_validation_defs(),
        build_schedule_defs(),
        build_sensor_defs(),
    )

    executor = _default_executor()

    defs_kwargs = {
        "assets": merged.assets,
        "asset_checks": merged.asset_checks,
        "schedules": merged.schedules,
        "sensors": merged.sensors,
        "resources": merged.resources,
        "jobs": merged.jobs,
    }

    if executor is not None:
        defs_kwargs["executor"] = executor

    return dg.Definitions(**defs_kwargs)


# Global defs object: The main Dagster Definitions instance used by the application
# This is imported by dagster.workspace.yaml and provides all assets, jobs, etc.
defs = _merged_definitions()
