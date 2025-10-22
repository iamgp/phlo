# __init__.py - Ingestion module initialization, aggregating data ingestion assets
# Defines the raw data ingestion layer that brings external data into the lakehouse
# using DLT for reliable, typed data loading

from __future__ import annotations

import dagster as dg

from cascade.defs.ingestion.dlt_assets import entries
from cascade.defs.ingestion.github_assets import github_user_events, github_repo_stats


# --- Aggregation Function ---
# Builds ingestion asset definitions
def build_defs() -> dg.Definitions:
    """Build ingestion definitions using dlt."""
    return dg.Definitions(assets=[entries, github_user_events, github_repo_stats])
