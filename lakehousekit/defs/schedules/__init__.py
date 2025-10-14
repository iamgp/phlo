from __future__ import annotations

import dagster as dg

from lakehousekit.defs.schedules.pipeline import (
    build_asset_jobs,
    build_schedules,
    build_sensors,
)


def build_defs() -> dg.Definitions:
    jobs = build_asset_jobs()

    schedules = build_schedules()
    sensors = build_sensors()

    return dg.Definitions(jobs=jobs, schedules=schedules, sensors=sensors)
