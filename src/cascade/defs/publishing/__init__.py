from __future__ import annotations

import dagster as dg

from cascade.defs.publishing.duckdb_to_postgres import (
    publish_glucose_marts_to_postgres,
)


def build_defs() -> dg.Definitions:
    return dg.Definitions(assets=[publish_glucose_marts_to_postgres])
