from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import dagster as dg
from dagster import FreshnessPolicy

from phlo.defs.partitions import daily_partition
from phlo.defs.resources.iceberg import IcebergResource
from phlo.ingestion.dlt_helpers import (
    get_branch_from_context,
    merge_to_iceberg,
    setup_dlt_pipeline,
    stage_to_parquet,
)
from phlo.schemas.converter import pandera_to_iceberg
from phlo.schemas.registry import TableConfig
from phlo.exceptions import (
    CascadeConfigError,
    CascadeSchemaError,
    CascadeCronError,
    suggest_similar_field_names,
    format_field_list,
)

_INGESTION_ASSETS: list[Any] = []


def _validate_cron_expression(cron: str | None) -> None:
    """
    Validate cron expression format.

    Args:
        cron: Cron expression string

    Raises:
        CascadeCronError: If cron expression is invalid
    """
    if not cron:
        return

    parts = cron.strip().split()

    # Cron should have 5 parts: minute hour day_of_month month day_of_week
    if len(parts) != 5:
        raise CascadeCronError(
            message=f"Invalid cron expression '{cron}'",
            suggestions=[
                "Cron format: [minute] [hour] [day_of_month] [month] [day_of_week]",
                'Examples: "0 */1 * * *" (hourly), "0 0 * * *" (daily), "*/15 * * * *" (every 15 min)',
                "Test your cron at: https://crontab.guru",
            ],
        )

    # Basic validation of each part
    for i, part in enumerate(parts):
        part_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        # Allow *, */N, N, N-M, N,M patterns
        if not (
            part == "*" or "/" in part or "-" in part or "," in part or part.isdigit()
        ):
            # Check if it's a day name (MON, TUE, etc.) for day_of_week
            if i == 4 and part.upper() in [
                "MON",
                "TUE",
                "WED",
                "THU",
                "FRI",
                "SAT",
                "SUN",
            ]:
                continue

            raise CascadeCronError(
                message=f"Invalid cron expression '{cron}': invalid {part_names[i]} value '{part}'",
            )


def _validate_unique_key_in_schema(
    unique_key: str,
    validation_schema: type[Any] | None,
) -> None:
    """
    Validate that unique_key exists in validation_schema fields.

    Args:
        unique_key: Field name used for deduplication
        validation_schema: Pandera DataFrameModel class

    Raises:
        CascadeSchemaError: If unique_key not found in schema
    """
    if validation_schema is None:
        # Can't validate without schema
        return

    try:
        # Get schema fields from Pandera DataFrameModel
        from typing import get_type_hints

        schema_fields = list(get_type_hints(validation_schema).keys())

        # Remove special Config class if present
        schema_fields = [f for f in schema_fields if f != "Config"]

        if unique_key not in schema_fields:
            # Generate "Did you mean?" suggestions
            suggestions_list = suggest_similar_field_names(unique_key, schema_fields)
            suggestions_list.append(
                f"Available fields: {format_field_list(schema_fields)}"
            )

            raise CascadeSchemaError(
                message=f"unique_key '{unique_key}' not found in schema '{validation_schema.__name__}'",
                suggestions=suggestions_list,
            )

    except CascadeSchemaError:
        raise
    except Exception as e:
        # If we can't validate (e.g., schema format issue), log but don't fail
        # The error will be caught at runtime if there's a real problem
        import warnings

        warnings.warn(
            f"Could not validate unique_key '{unique_key}' against schema: {e}",
            UserWarning,
        )


def phlo_ingestion(
    table_name: str,
    unique_key: str,
    group: str,
    validation_schema: type[Any] | None = None,
    iceberg_schema: Any | None = None,
    partition_spec: Any | None = None,
    cron: str | None = None,
    freshness_hours: tuple[int, int] | None = None,
    max_runtime_seconds: int = 300,
    max_retries: int = 3,
    retry_delay_seconds: int = 30,
    validate: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for creating Cascade ingestion assets with minimal boilerplate.

    Define schemas inline with your asset - no central registry required!

    Automatically handles:
    - Branch extraction from context
    - Table name generation (namespace.table_name)
    - DLT pipeline directory setup
    - Pandera validation (if validation_schema provided)
    - DLT staging to parquet
    - Iceberg table creation
    - Merge to Iceberg with deduplication
    - Timing instrumentation
    - MaterializeResult generation

    Args:
        table_name: Iceberg table name (without namespace)
        unique_key: Column name for deduplication (e.g., "id", "_id")
        group: Dagster asset group name
        validation_schema: Pandera DataFrameModel class (optional but recommended)
        iceberg_schema: PyIceberg Schema (optional - auto-generated from validation_schema if not provided)
        partition_spec: Iceberg partition spec (optional)
        cron: Cron schedule for automation (e.g., "0 */1 * * *")
        freshness_hours: Tuple of (warn_window_hours, fail_window_hours)
        max_runtime_seconds: Maximum runtime before timeout
        max_retries: Number of retry attempts on failure
        retry_delay_seconds: Delay between retries
        validate: Whether to validate data with Pandera schema

    Returns:
        Decorator function that wraps user's fetch function

    Example:
        # With Pandera validation (iceberg_schema auto-generated):
        @phlo_ingestion(
            table_name="github_user_events",
            unique_key="id",
            validation_schema=RawGitHubUserEvents,
            group="github",
            cron="0 */1 * * *",
            freshness_hours=(1, 24),
        )
        def github_user_events(partition_date: str):
            return rest_api({...})
    """
    # Validate decorator parameters at definition time (fast feedback!)
    _validate_cron_expression(cron)
    _validate_unique_key_in_schema(unique_key, validation_schema)

    # Auto-generate PyIceberg schema from Pandera if not provided
    if iceberg_schema is None and validation_schema is not None:
        iceberg_schema = pandera_to_iceberg(validation_schema)
    elif iceberg_schema is None:
        raise CascadeConfigError(
            message="Missing required schema parameter",
            suggestions=[
                "Add validation_schema parameter (recommended): validation_schema=MyPanderaSchema",
                "Or add iceberg_schema parameter (manual): iceberg_schema=IcebergSchema(...)",
                "Recommended: Use validation_schema - Iceberg schema will be auto-generated",
            ],
        )

    # Create table config from inline parameters
    table_config = TableConfig(
        table_name=table_name,
        iceberg_schema=iceberg_schema,
        validation_schema=validation_schema,  # type: ignore
        unique_key=unique_key,
        group_name=group,
        partition_spec=partition_spec,
    )

    def decorator(func: Callable[..., Any]) -> Any:
        @dg.asset(
            name=f"dlt_{table_config.table_name}",
            group_name=group,
            partitions_def=daily_partition,
            description=func.__doc__
            or f"Ingests {table_config.table_name} data to Iceberg",
            kinds={"dlt", "iceberg"},
            op_tags={"dagster/max_runtime": max_runtime_seconds},
            retry_policy=dg.RetryPolicy(
                max_retries=max_retries, delay=retry_delay_seconds
            ),
            automation_condition=(
                dg.AutomationCondition.on_cron(cron) if cron else None
            ),
            freshness_policy=(
                FreshnessPolicy.time_window(
                    warn_window=timedelta(hours=freshness_hours[0]),
                    fail_window=timedelta(hours=freshness_hours[1]),
                )
                if freshness_hours
                else None
            ),
        )
        def wrapper(context, iceberg: IcebergResource) -> dg.MaterializeResult:
            partition_date = context.partition_key
            pipeline_name = (
                f"{table_config.table_name}_{partition_date.replace('-', '_')}"
            )
            branch_name = get_branch_from_context(context)

            context.log.info(f"Starting ingestion for partition {partition_date}")
            context.log.info(f"Ingesting to branch: {branch_name}")
            context.log.info(f"Target table: {table_config.full_table_name}")

            start_time = time.time()

            try:
                context.log.info("Calling user function to get DLT source...")
                dlt_source = func(partition_date)

                if dlt_source is None:
                    context.log.info(
                        f"No data for partition {partition_date}, skipping"
                    )
                    return dg.MaterializeResult(
                        metadata={
                            "branch": branch_name,
                            "partition_date": dg.MetadataValue.text(partition_date),
                            "rows_loaded": dg.MetadataValue.int(0),
                            "status": dg.MetadataValue.text("no_data"),
                        }
                    )

                pipeline, local_staging_root = setup_dlt_pipeline(
                    pipeline_name=pipeline_name,
                    dataset_name=group,
                )

                parquet_path, dlt_elapsed = stage_to_parquet(
                    context=context,
                    pipeline=pipeline,
                    dlt_source=dlt_source,
                    local_staging_root=local_staging_root,
                )

                merge_metrics = merge_to_iceberg(
                    context=context,
                    iceberg=iceberg,
                    table_config=table_config,
                    parquet_path=parquet_path,
                    branch_name=branch_name,
                )

                total_elapsed = time.time() - start_time
                context.log.info(
                    f"Ingestion completed successfully in {total_elapsed:.2f}s"
                )

                return dg.MaterializeResult(
                    metadata={
                        "branch": branch_name,
                        "partition_date": dg.MetadataValue.text(partition_date),
                        "rows_inserted": dg.MetadataValue.int(
                            merge_metrics["rows_inserted"]
                        ),
                        "rows_deleted": dg.MetadataValue.int(
                            merge_metrics["rows_deleted"]
                        ),
                        "unique_key": dg.MetadataValue.text(table_config.unique_key),
                        "table_name": dg.MetadataValue.text(
                            table_config.full_table_name
                        ),
                        "dlt_elapsed_seconds": dg.MetadataValue.float(dlt_elapsed),
                        "total_elapsed_seconds": dg.MetadataValue.float(total_elapsed),
                    }
                )

            except Exception as e:
                context.log.error(
                    f"Ingestion failed for partition {partition_date}: {e}"
                )
                raise RuntimeError(
                    f"Ingestion failed for partition {partition_date}: {e}"
                ) from e

        _INGESTION_ASSETS.append(wrapper)
        return wrapper

    return decorator


def get_ingestion_assets() -> list[Any]:
    """
    Get all assets registered with @phlo_ingestion decorator.

    Returns:
        List of Dagster asset definitions
    """
    return _INGESTION_ASSETS.copy()
