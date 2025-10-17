from __future__ import annotations

import platform

import dagster as dg

from cascade.config import config
from cascade.defs.ingestion import build_defs as build_ingestion_defs
from cascade.defs.jobs import build_defs as build_job_defs
from cascade.defs.nessie import build_defs as build_nessie_defs
from cascade.defs.publishing import build_defs as build_publishing_defs
from cascade.defs.quality import build_defs as build_quality_defs
from cascade.defs.resources import build_defs as build_resource_defs
from cascade.defs.schedules import build_defs as build_schedule_defs
from cascade.defs.transform import build_defs as build_transform_defs


def _default_executor() -> dg.ExecutorDefinition | None:
    """
    Choose an executor suited to the current environment.

    Multiprocessing is desirable on Linux servers, but DuckDB has been crashing (SIGBUS) when the
    container runs under Docker Desktop/Colima on macOS. Fall back to the in-process executor on
    macOS, and allow an override via `CASCADE_FORCE_IN_PROCESS_EXECUTOR` if someone hits the
    same issue elsewhere.

    Updated: Testing DuckDB 1.4.1 which has improved multiprocessing/fork safety.
    """
    if config.cascade_force_in_process_executor:
        return dg.in_process_executor

    if config.cascade_force_multiprocess_executor:
        return dg.multiprocess_executor.configured({"max_concurrent": 4})

    if platform.system() == "Darwin":
        return dg.in_process_executor

    return dg.multiprocess_executor.configured({"max_concurrent": 4})


def _merged_definitions() -> dg.Definitions:
    merged = dg.Definitions.merge(
        build_resource_defs(),
        build_ingestion_defs(),
        build_transform_defs(),
        build_publishing_defs(),
        build_quality_defs(),
        build_nessie_defs(),
        build_schedule_defs(),
        build_job_defs(),
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


defs = _merged_definitions()
