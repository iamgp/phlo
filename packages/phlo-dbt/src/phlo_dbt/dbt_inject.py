"""Helpers to inject stable row identifiers into dbt-managed tables."""

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

    Args:
        trino_connection: Open Trino connection used for DDL and DML statements.
        catalog: Trino catalog name.
        schema: Trino schema name.
        table: Target table name.
        context: Optional runtime context with a logger.

    Returns:
        Result metadata including updated row count and whether the table was skipped.
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

    Args:
        trino_connection: Open Trino connection used for table updates.
        run_results: Parsed dbt `run_results.json` payload.
        catalog: Trino catalog containing dbt target schemas.
        context: Optional runtime context with a logger.

    Returns:
        Mapping of model name to per-model injection result or error payload.
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
