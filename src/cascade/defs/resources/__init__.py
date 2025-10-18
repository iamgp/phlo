from __future__ import annotations

import dagster as dg
from dagster_dbt import DbtCliResource

from cascade.config import config
from cascade.defs.resources.iceberg import IcebergResource
from cascade.defs.resources.trino import TrinoResource

__all__ = ["IcebergResource", "TrinoResource", "NessieResource"]


# NessieResource is defined in cascade.defs.nessie but re-exported here for convenience
def __getattr__(name: str):
    if name == "NessieResource":
        from cascade.defs.nessie import NessieResource
        return NessieResource
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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

    Resources are configured with default branch (main) but can be overridden
    at the job level for dev/prod workflows via config.

    Returns:
        Definitions containing configured resources:
        - dbt: For SQL-based data transformations
        - trino: Query engine used for Iceberg reads/writes (branch-aware)
        - iceberg: PyIceberg/Nessie catalog helper (branch-aware)

    Note: nessie resource is provided by cascade.defs.nessie module
    """
    iceberg_resource = IcebergResource()
    trino_resource = TrinoResource()

    return dg.Definitions(
        resources={
            "dbt": _build_dbt_resource(),
            "trino": trino_resource,
            "iceberg": iceberg_resource,
        }
    )
