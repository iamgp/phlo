"""Helpers to inject stable row identifiers into dbt-managed tables.

This module provides utilities for adding `_phlo_row_id` columns to dbt-generated
tables. These stable identifiers enable reliable row-level tracking and lineage
across the data pipeline, particularly useful for incremental processing and
auditing.

Example:
    >>> from phlo_dbt.dbt_inject import inject_row_ids_to_table
    >>> result = inject_row_ids_to_table(
    ...     trino_connection=conn,
    ...     catalog="iceberg",
    ...     schema="marts",
    ...     table="mrt_orders"
    ... )
    >>> print(f"Updated {result['rows_updated']} rows")
    >>>
    >>> # Or inject for all models from a dbt run
    >>> from phlo_dbt.dbt_inject import inject_row_ids_for_dbt_run
    >>> results = inject_row_ids_for_dbt_run(
    ...     trino_connection=conn,
    ...     run_results=run_results_data
    ... )

"""

from __future__ import annotations

from typing import Any

from phlo.logging import get_logger

logger = get_logger(__name__)


def _resolve_logger(context: Any | None) -> Any:
    """Resolve a logger from optional context, defaulting to module logger."""
    if context is None:
        return logger
    context_logger = getattr(context, "log", None)
    if context_logger is None:
        return logger
    return context_logger


def inject_row_ids_to_table(
    *,
    trino_connection: Any,
    catalog: str,
    schema: str,
    table: str,
    context: Any | None = None,
) -> dict[str, Any]:
    """Add `_phlo_row_id` to a table and backfill missing values.

    Checks if the `_phlo_row_id` column exists in the specified table. If not,
    adds the column and populates it with UUID values for all existing rows.
    This provides stable row identifiers for lineage and auditing.

    Args:
        trino_connection: Open Trino connection used for DDL and DML statements.
            Must support cursor() method and execute() operations.
        catalog: Trino catalog name (e.g., "iceberg").
        schema: Trino schema name (e.g., "marts", "silver").
        table: Target table name to modify.
        context: Optional runtime context with a logger (e.g., Dagster context).
            Used for structured logging during execution.

    Returns:
        Result metadata dictionary containing:
            - rows_updated: Number of rows that received new IDs
            - skipped: Boolean indicating if column already existed

    Raises:
        Exception: Any database errors during DDL or DML operations.

    Example:
        >>> import trino
        >>> conn = trino.dbapi.connect(host="trino", port=8080, catalog="iceberg")
        >>> result = inject_row_ids_to_table(
        ...     trino_connection=conn,
        ...     catalog="iceberg",
        ...     schema="marts",
        ...     table="mrt_orders"
        ... )
        >>> if result["skipped"]:
        ...     print("Column already exists, no changes made")
        ... else:
        ...     print(f"Added IDs to {result['rows_updated']} rows")

    """
    cursor = trino_connection.cursor()
    logger_ = _resolve_logger(context)

    fqtn = f"{catalog}.{schema}.{table}"
    rows_updated: int | None = None
    logger_.info(
        "dbt_row_id_injection_started",
        catalog=catalog,
        schema=schema,
        table=table,
        fqtn=fqtn,
    )

    try:
        cursor.execute(f"DESCRIBE {fqtn}")
        column_rows = cursor.fetchall()
        column_names = {row[0] for row in column_rows}

        if "_phlo_row_id" in column_names:
            logger_.info(
                "dbt_row_id_injection_skipped",
                catalog=catalog,
                schema=schema,
                table=table,
                fqtn=fqtn,
                rows_updated=0,
                reason="row_id_column_exists",
            )
            return {"rows_updated": 0, "skipped": True}

        cursor.execute(f"ALTER TABLE {fqtn} ADD COLUMN _phlo_row_id VARCHAR")

        cursor.execute(f"SELECT COUNT(*) FROM {fqtn}")
        (row_count,) = cursor.fetchone()
        rows_updated = int(row_count)

        cursor.execute(
            f"UPDATE {fqtn} SET _phlo_row_id = CAST(uuid() AS VARCHAR) WHERE _phlo_row_id IS NULL"
        )

        logger_.info(
            "dbt_row_id_injection_finished",
            catalog=catalog,
            schema=schema,
            table=table,
            fqtn=fqtn,
            rows_updated=rows_updated,
            skipped=False,
        )
        return {"rows_updated": rows_updated}
    except Exception as exc:
        logger_.error(
            "dbt_row_id_injection_failed",
            catalog=catalog,
            schema=schema,
            table=table,
            fqtn=fqtn,
            rows_updated=rows_updated,
            error=str(exc),
            exc_info=True,
        )
        raise


def inject_row_ids_for_dbt_run(
    *,
    trino_connection: Any,
    run_results: dict[str, Any],
    catalog: str = "iceberg",
    context: Any | None = None,
) -> dict[str, Any]:
    """Inject `_phlo_row_id` into successful dbt model outputs.

    Processes dbt run_results.json to identify successfully built models and
    injects row IDs into each one. Uses model name prefixes to determine the
    appropriate schema:
    - stg_* -> silver
    - dim_*, fct_* -> gold
    - mrt_* -> marts
    - others -> silver

    Args:
        trino_connection: Open Trino connection for table operations.
        run_results: Parsed dbt run_results.json payload containing execution results.
        catalog: Trino catalog name (default: "iceberg").
        context: Optional runtime context with logger for structured logging.

    Returns:
        Mapping of model names to their injection results. Each entry contains
        either the injection result dict or an error message if injection failed.

    Example:
        >>> import json
        >>> from pathlib import Path
        >>>
        >>> run_results = json.loads(
        ...     Path("target/run_results.json").read_text()
        ... )
        >>> results = inject_row_ids_for_dbt_run(
        ...     trino_connection=conn,
        ...     run_results=run_results,
        ...     catalog="iceberg"
        ... )
        >>>
        >>> for model, result in results.items():
        ...     if "error" in result:
        ...         print(f"{model}: FAILED - {result['error']}")
        ...     else:
        ...         print(f"{model}: {result['rows_updated']} rows updated")

    """
    results: dict[str, Any] = {}

    for result in run_results.get("results", []):
        if result.get("status") != "success":
            continue

        unique_id = result.get("unique_id", "")
        model_name = unique_id.split(".")[-1] if unique_id else ""
        if not model_name:
            continue

        if model_name.startswith("stg_"):
            schema = "silver"
        elif model_name.startswith(("dim_", "fct_")):
            schema = "gold"
        elif model_name.startswith("mrt_"):
            schema = "marts"
        else:
            schema = "silver"

        try:
            results[model_name] = inject_row_ids_to_table(
                trino_connection=trino_connection,
                catalog=catalog,
                schema=schema,
                table=model_name,
                context=context,
            )
        except Exception as exc:
            results[model_name] = {"error": str(exc)}

    return results
