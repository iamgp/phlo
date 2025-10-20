# __init__.py - Publishing module initialization, aggregating data publishing assets
# Defines the final layer that publishes processed marts to downstream systems
# like PostgreSQL for fast BI queries and external consumption

from __future__ import annotations

import dagster as dg

from cascade.defs.publishing.trino_to_postgres import (
    publish_glucose_marts_to_postgres,
)


# --- Aggregation Function ---
# Builds publishing asset definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=[publish_glucose_marts_to_postgres])
