from __future__ import annotations

import dagster as dg

from cascade.defs.transform.dbt import all_dbt_assets


def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=[all_dbt_assets])
