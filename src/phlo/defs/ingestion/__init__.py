# __init__.py - Ingestion module initialization, aggregating data ingestion assets
# Defines the raw data ingestion layer that brings external data into the lakehouse
# using DLT for reliable, typed data loading

from __future__ import annotations

import dagster as dg

from phlo.ingestion import get_ingestion_assets

# Import all asset modules to trigger decorator registration
from phlo.defs.ingestion import github as github
from phlo.defs.ingestion import nightscout as nightscout


def build_defs() -> dg.Definitions:
    """
    Build ingestion definitions using phlo_ingestion decorator.

    Assets are automatically discovered from all modules that use the
    @phlo_ingestion decorator. No manual registration required.
    """
    return dg.Definitions(assets=get_ingestion_assets())
