# __init__.py - Ingestion module initialization, aggregating data ingestion assets
# Defines the raw data ingestion layer that brings external data into the lakehouse
# using DLT for reliable, typed data loading

from __future__ import annotations

import dagster as dg

from cascade.ingestion import get_ingestion_assets

# Import all asset modules to trigger decorator registration
from cascade.defs.ingestion import github  # noqa: F401
from cascade.defs.ingestion import nightscout  # noqa: F401


def build_defs() -> dg.Definitions:
    """
    Build ingestion definitions using cascade_ingestion decorator.

    Assets are automatically discovered from all modules that use the
    @cascade_ingestion decorator. No manual registration required.
    """
    return dg.Definitions(assets=get_ingestion_assets())
