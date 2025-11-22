"""
Sensors package for Cascade data pipeline automation.

Provides sensors for:
- Automatic branch creation when jobs start
- Automatic branch promotion after all checks pass
- Branch cleanup after retention period
"""

import dagster as dg
from phlo.defs.sensors.branch_lifecycle import (
    branch_creation_sensor,
    auto_promotion_sensor,
    branch_cleanup_sensor,
)

__all__ = [
    "branch_creation_sensor",
    "auto_promotion_sensor",
    "branch_cleanup_sensor",
]


def build_defs() -> dg.Definitions:
    """Build sensor definitions for automated pipeline management."""
    return dg.Definitions(
        sensors=[
            branch_creation_sensor,
            auto_promotion_sensor,
            branch_cleanup_sensor,
        ],
    )
