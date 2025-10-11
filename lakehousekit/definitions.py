from __future__ import annotations

import dagster as dg

from lakehousekit.defs.ingestion import build_defs as build_ingestion_defs
from lakehousekit.defs.metadata import build_defs as build_metadata_defs
from lakehousekit.defs.publishing import build_defs as build_publishing_defs
from lakehousekit.defs.quality import build_defs as build_quality_defs
from lakehousekit.defs.resources import build_defs as build_resource_defs
from lakehousekit.defs.schedules import build_defs as build_schedule_defs
from lakehousekit.defs.transform import build_defs as build_transform_defs


def _merged_definitions() -> dg.Definitions:
    merged = dg.Definitions.merge(
        build_resource_defs(),
        build_ingestion_defs(),
        build_transform_defs(),
        build_publishing_defs(),
        build_metadata_defs(),
        build_quality_defs(),
        build_schedule_defs(),
    )

    # Use in-process executor to avoid Great Expectations subprocess crashes
    return dg.Definitions(
        assets=merged.assets,
        asset_checks=merged.asset_checks,
        schedules=merged.schedules,
        sensors=merged.sensors,
        resources=merged.resources,
        jobs=merged.jobs,
        executor=dg.in_process_executor,
    )


defs = _merged_definitions()
