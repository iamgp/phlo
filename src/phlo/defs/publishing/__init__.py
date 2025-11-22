# __init__.py - Publishing module initialization, aggregating data publishing assets
# Defines the final layer that publishes processed marts to downstream systems
# like PostgreSQL for fast BI queries and external consumption

from __future__ import annotations

import dagster as dg

from phlo.defs.publishing.trino_to_postgres import PUBLISHING_ASSETS


# --- Aggregation Function ---
# Builds publishing asset definitions
def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=PUBLISHING_ASSETS)
