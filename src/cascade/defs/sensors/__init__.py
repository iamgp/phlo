"""
Sensors package for Cascade data pipeline automation.

Provides sensors for:
- Automatic branch promotion after validation
- Branch cleanup after retention period
- Failure monitoring
"""

from cascade.defs.sensors.promotion_sensor import auto_promotion_sensor, branch_cleanup_sensor

__all__ = [
    "auto_promotion_sensor",
    "branch_cleanup_sensor",
]
