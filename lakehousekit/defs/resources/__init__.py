from __future__ import annotations

import dagster as dg
from dagster_dbt import DbtCliResource

from lakehousekit.config import config
from lakehousekit.defs.resources.duckdb import DuckDBResource

__all__ = ["DuckDBResource"]


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
        - dbt: For SQL-based data transformations
        - duckdb: For analytics database connections
    """
    return dg.Definitions(
        resources={
            "dbt": _build_dbt_resource(),
            "duckdb": DuckDBResource(),
        }
    )
