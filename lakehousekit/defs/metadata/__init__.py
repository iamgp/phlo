from __future__ import annotations

import dagster as dg

from lakehousekit.defs.metadata.datahub import ingest_dbt_to_datahub


def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=[ingest_dbt_to_datahub])
