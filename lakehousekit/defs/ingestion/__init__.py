from __future__ import annotations

import dagster as dg

from lakehousekit.defs.ingestion.dlt_assets import nightscout_entries

# Bioreactor assets disabled - focusing on Nightscout workflow
# from lakehousekit.defs.ingestion.raw import raw_bioreactor_data


def build_defs() -> dg.Definitions:
    """Build ingestion definitions using dlt."""
    return dg.Definitions(assets=[nightscout_entries])
