# __init__.py - Ingestion module initialization
# The framework discovers ingestion assets from user workflows automatically

from __future__ import annotations

import dagster as dg

from phlo.ingestion import get_ingestion_assets


def build_defs() -> dg.Definitions:
    """
    Build ingestion definitions using phlo_ingestion decorator.

    Assets are automatically discovered from user workflows that use the
    @phlo_ingestion decorator. No manual registration required.
    """
    return dg.Definitions(assets=get_ingestion_assets())
