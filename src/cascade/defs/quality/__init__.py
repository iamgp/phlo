# __init__.py - Quality module initialization, aggregating data quality checks
# Defines asset checks that validate data integrity and business rules
# throughout the lakehouse transformation pipeline

from __future__ import annotations

import dagster as dg

from cascade.defs.quality.nightscout import nightscout_glucose_quality_check


# --- Aggregation Function ---
# Builds quality check definitions for data validation
def build_defs() -> dg.Definitions:
    return dg.Definitions(asset_checks=[nightscout_glucose_quality_check])
