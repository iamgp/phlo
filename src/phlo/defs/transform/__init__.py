# __init__.py - Transform module initialization, aggregating dbt transformation assets
# Defines the SQL-based data transformation layer using dbt for bronze, silver, and gold
# layer processing of raw data into analytics-ready datasets

from __future__ import annotations

import dagster as dg

from phlo.defs.transform.dbt import build_defs as build_dbt_defs


# --- Aggregation Function ---
# Builds transformation asset definitions
def build_defs() -> dg.Definitions:
    return build_dbt_defs()
