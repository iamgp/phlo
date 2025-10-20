# __init__.py - Transform module initialization, aggregating dbt transformation assets
# Defines the SQL-based data transformation layer using dbt for bronze, silver, and gold
# layer processing of raw data into analytics-ready datasets

from __future__ import annotations

import dagster as dg

from cascade.defs.transform.dbt import all_dbt_assets


# --- Aggregation Function ---
# Builds transformation asset definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=[all_dbt_assets])
