from __future__ import annotations

import dagster as dg

from lakehousekit.defs.ingestion.dlt_assets import entries


def build_defs() -> dg.Definitions:
    """Build ingestion definitions using dlt."""
    return dg.Definitions(assets=[entries])
