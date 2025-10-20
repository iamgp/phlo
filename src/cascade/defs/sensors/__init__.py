# __init__.py - Sensors module initialization, aggregating monitoring and alerting sensors
# Defines sensors that monitor pipeline health, data freshness, and trigger
# automated workflows for observability and incident response

from __future__ import annotations

import dagster as dg

from cascade.defs.sensors.failure_monitoring import (
    iceberg_freshness_sensor,
    pipeline_failure_sensor,
    pipeline_success_sensor,
)


# --- Aggregation Function ---
# Builds sensor definitions for pipeline monitoring
def build_defs() -> dg.Definitions:
    """Build sensors for observability and monitoring."""
    return dg.Definitions(
        sensors=[
            pipeline_failure_sensor,
            pipeline_success_sensor,
            iceberg_freshness_sensor,
        ]
    )


# Public API exports
__all__ = [
    "build_defs",
    "pipeline_failure_sensor",
    "pipeline_success_sensor",
    "iceberg_freshness_sensor",
]
