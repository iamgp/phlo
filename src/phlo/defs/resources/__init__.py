# __init__.py - Resources module initialization, providing configured Dagster resources
# Sets up all external service integrations (dbt, Trino, Iceberg, Nessie) with
# appropriate configurations for the lakehouse data pipeline

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dagster as dg
from dagster_dbt import DbtCliResource

from phlo.config import config
from phlo.defs.resources.iceberg import IcebergResource
from phlo.defs.resources.trino import TrinoResource
from phlo.defs.validation.dbt_validator import DBTValidatorResource
from phlo.defs.validation.freshness_validator import FreshnessValidatorResource
from phlo.defs.validation.schema_validator import SchemaCompatibilityValidatorResource

# Public API exports
__all__ = ["IcebergResource", "NessieResource", "TrinoResource"]

if TYPE_CHECKING:
    from phlo.defs.nessie import NessieResource


# --- Re-exports and Lazy Imports ---
# NessieResource is defined in phlo.defs.nessie but re-exported here for convenience
def __getattr__(name: str):
    if name == "NessieResource":
        from phlo.defs.nessie import NessieResource

        return NessieResource
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# --- Resource Builder Functions ---
# Helper functions to configure external service resources
def _build_dbt_resource() -> DbtCliResource | None:
    """
    Build the dbt CLI resource for data transformations.

    Returns:
        Configured DbtCliResource if dbt directories exist, None otherwise
    """
    # Check if dbt directories exist (optional for user projects)
    if not config.dbt_project_path.exists():
        return None

    return DbtCliResource(
        project_dir=str(config.dbt_project_path),
        profiles_dir=str(config.dbt_profiles_path),
    )


# --- Aggregation Function ---
# Creates unified resource definitions for the pipeline
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
        - dbt_validator: dbt test execution and parsing
        - freshness_validator: Data freshness checks
        - schema_validator: Schema compatibility validation

    Note: nessie resource is provided by phlo.defs.nessie module
    """
    iceberg_resource = IcebergResource()
    trino_resource = TrinoResource()

    # Build resources dict, making dbt optional
    resources: dict[str, Any] = {
        "trino": trino_resource,
        "iceberg": iceberg_resource,
        "dbt_validator": DBTValidatorResource(),
        "freshness_validator": FreshnessValidatorResource(),
        "schema_validator": SchemaCompatibilityValidatorResource(),
    }

    # Add dbt resource if available
    dbt_resource = _build_dbt_resource()
    if dbt_resource is not None:
        resources["dbt"] = dbt_resource

    return dg.Definitions(resources=resources)
