from __future__ import annotations

import dagster as dg

from lakehousekit.defs.schedules.pipeline import build_asset_jobs, build_schedules


def build_defs() -> dg.Definitions:
    jobs = build_asset_jobs()

    transform_job = next(job for job in jobs if job.name == "transform_dbt_models")
    schedules = build_schedules(transform_job)

    return dg.Definitions(jobs=jobs, schedules=schedules)
