from __future__ import annotations

import dagster as dg

from cascade.defs.sensors.failure_monitoring import (
    iceberg_freshness_sensor,
    pipeline_failure_sensor,
    pipeline_success_sensor,
)


def build_defs() -> dg.Definitions:
    """Build sensors for observability and monitoring."""
    return dg.Definitions(
        sensors=[
            pipeline_failure_sensor,
            pipeline_success_sensor,
            iceberg_freshness_sensor,
        ]
    )


__all__ = [
    "build_defs",
    "pipeline_failure_sensor",
    "pipeline_success_sensor",
    "iceberg_freshness_sensor",
]
