# __init__.py - Schedules module initialization, aggregating pipeline orchestration definitions
# Combines asset jobs, sensors, and schedules into a unified Dagster definitions object
# for the data pipeline workflow management

from __future__ import annotations

import dagster as dg

from cascade.defs.schedules.pipeline import (
    build_asset_jobs,
    build_schedules,
    build_sensors,
)


# --- Aggregation Function ---
# Combines all schedule-related definitions into a single Definitions object
def build_defs() -> dg.Definitions:
    jobs = build_asset_jobs()

    schedules = build_schedules()
    sensors = build_sensors()

    return dg.Definitions(jobs=jobs, schedules=schedules, sensors=sensors)
