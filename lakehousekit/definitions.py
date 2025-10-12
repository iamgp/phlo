from __future__ import annotations

import platform

import dagster as dg

from lakehousekit.config import config
from lakehousekit.defs.ingestion import build_defs as build_ingestion_defs
from lakehousekit.defs.metadata import build_defs as build_metadata_defs
from lakehousekit.defs.publishing import build_defs as build_publishing_defs
from lakehousekit.defs.quality import build_defs as build_quality_defs
from lakehousekit.defs.resources import build_defs as build_resource_defs
from lakehousekit.defs.schedules import build_defs as build_schedule_defs
from lakehousekit.defs.transform import build_defs as build_transform_defs


def _default_executor() -> dg.ExecutorDefinition | None:
    """
    Choose an executor suited to the current environment.

    Multiprocessing is desirable on Linux servers, but DuckDB has been crashing (SIGBUS) when the
    container runs under Docker Desktop/Colima on macOS. Fall back to the in-process executor on
    macOS, and allow an override via `LAKEHOUSEKIT_FORCE_IN_PROCESS_EXECUTOR` if someone hits the
    same issue elsewhere.
    """
    if config.lakehousekit_force_in_process_executor:
        return dg.in_process_executor

    if config.lakehousekit_force_multiprocess_executor:
        return None

    if platform.system() == "Darwin":
        return dg.in_process_executor

    return None


def _merged_definitions() -> dg.Definitions:
    merged = dg.Definitions.merge(
        build_resource_defs(),
        build_ingestion_defs(),
        build_transform_defs(),
        build_publishing_defs(),
        build_metadata_defs(),
        build_quality_defs(),
        build_schedule_defs(),
    )

    executor = _default_executor()

    defs_kwargs = dict(
        assets=merged.assets,
        asset_checks=merged.asset_checks,
        schedules=merged.schedules,
        sensors=merged.sensors,
        resources=merged.resources,
        jobs=merged.jobs,
    )

    if executor is not None:
        defs_kwargs["executor"] = executor

    return dg.Definitions(**defs_kwargs)


defs = _merged_definitions()
