from __future__ import annotations

import dagster as dg

from cascade.defs.partitions import daily_partition


nightscout_job = dg.define_asset_job(
    name="nightscout_pipeline",
    selection=["entries", "group:bronze", "group:silver", "group:gold", "group:publish"],
    partitions_def=daily_partition,
)


def build_defs() -> dg.Definitions:
    return dg.Definitions(jobs=[nightscout_job])
