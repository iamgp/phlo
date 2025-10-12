from __future__ import annotations

import dagster as dg
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCliResource

from lakehousekit.config import config
from lakehousekit.defs.resources.duckdb import DuckDBResource

__all__ = ["DuckDBResource"]


def _build_airbyte_resource() -> AirbyteResource:
    return AirbyteResource(host=config.airbyte_host, port=str(config.airbyte_api_port))


def _build_dbt_resource() -> DbtCliResource:
    return DbtCliResource(
        project_dir=str(config.dbt_project_path),
        profiles_dir=str(config.dbt_profiles_path),
    )


def build_defs() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "airbyte": _build_airbyte_resource(),
            "dbt": _build_dbt_resource(),
            "duckdb": DuckDBResource(),
        }
    )
