from __future__ import annotations

import dagster as dg
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCliResource

from lakehousekit.config import config
from lakehousekit.defs.resources.duckdb import DuckDBResource

__all__ = ["DuckDBResource"]


def _build_airbyte_resource() -> AirbyteResource:
    """
    Build the Airbyte resource for data ingestion.

    Returns:
        Configured AirbyteResource using host and port from config
    """
    return AirbyteResource(host=config.airbyte_host, port=str(config.airbyte_api_port))


def _build_dbt_resource() -> DbtCliResource:
    """
    Build the dbt CLI resource for data transformations.

    Returns:
        Configured DbtCliResource using project and profiles paths from config
    """
    return DbtCliResource(
        project_dir=str(config.dbt_project_path),
        profiles_dir=str(config.dbt_profiles_path),
    )


def build_defs() -> dg.Definitions:
    """
    Build Dagster resource definitions for the lakehouse platform.

    Returns:
        Definitions containing configured resources:
        - airbyte: For data ingestion from external sources
        - dbt: For SQL-based data transformations
        - duckdb: For analytics database connections
    """
    return dg.Definitions(
        resources={
            "airbyte": _build_airbyte_resource(),
            "dbt": _build_dbt_resource(),
            "duckdb": DuckDBResource(),
        }
    )
