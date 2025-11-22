# __init__.py - Schedules module initialization, aggregating pipeline orchestration definitions
# Combines asset jobs, sensors, and schedules into a unified Dagster definitions object
# for the data pipeline workflow management

from __future__ import annotations

import dagster as dg

from phlo.defs.jobs import JOBS
from phlo.defs.sensors.sensors import build_sensors as build_transform_sensors
from phlo.defs.schedules.schedules import create_schedules


def build_schedules() -> list[dg.ScheduleDefinition]:
    """Build schedules using jobs from the jobs module."""
    return create_schedules(JOBS)


# --- Aggregation Function ---
# Combines all schedule-related definitions into a single Definitions object
def build_defs() -> dg.Definitions:
    """
    Build schedules and transform sensors.

    Note: Promotion and cleanup sensors are defined in phlo.defs.sensors
    """
    schedules = build_schedules()
    transform_sensors = build_transform_sensors()

    return dg.Definitions(jobs=JOBS, schedules=schedules, sensors=transform_sensors)
