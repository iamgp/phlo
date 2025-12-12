"""Row ID injection for dbt-transformed tables.

Automatically adds _phlo_row_id column to dbt tables after materialization.
Uses Trino/Iceberg ALTER TABLE and UPDATE to populate UUIDs.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def inject_row_ids_to_table(
    trino_connection: Any,
    catalog: str,
    schema: str,
    table: str,
    context: Any = None,
) -> dict[str, int]:
    """Inject _phlo_row_id column to a dbt-materialized table.

    This function is called after dbt materializes a table to add
    the lineage tracking column with UUIDs.

    Args:
        trino_connection: Trino connection object
        catalog: Iceberg catalog name (e.g., "iceberg")
        schema: Schema name (e.g., "silver")
        table: Table name (e.g., "stg_github_events")
        context: Optional Dagster context for logging

    Returns:
        Dict with rows_updated count
    """
    full_table = f"{catalog}.{schema}.{table}"
    cursor = trino_connection.cursor()

    def log(msg: str):
        if context:
            context.log.info(msg)
        else:
            logger.info(msg)

    try:
        # Check if column already exists
        cursor.execute(f"DESCRIBE {full_table}")
        columns = {row[0] for row in cursor.fetchall()}

        if "_phlo_row_id" in columns:
            log(f"[inject_row_ids] {full_table} already has _phlo_row_id column")
            return {"rows_updated": 0}

        # Add the column
        log(f"[inject_row_ids] Adding _phlo_row_id column to {full_table}")
        cursor.execute(f"ALTER TABLE {full_table} ADD COLUMN _phlo_row_id VARCHAR")

        # Update with UUIDs for rows that don't have one
        log(f"[inject_row_ids] Populating _phlo_row_id with UUIDs in {full_table}")
        cursor.execute(f"""
            UPDATE {full_table}
            SET _phlo_row_id = cast(uuid() as varchar)
            WHERE _phlo_row_id IS NULL
        """)

        # Get count of updated rows
        cursor.execute(f"SELECT count(*) FROM {full_table} WHERE _phlo_row_id IS NOT NULL")
        row_count = cursor.fetchone()[0]

        log(f"[inject_row_ids] Injected _phlo_row_id to {row_count} rows in {full_table}")
        return {"rows_updated": row_count}

    except Exception as e:
        log(f"[inject_row_ids] Error injecting row IDs to {full_table}: {e}")
        raise
    finally:
        cursor.close()


def inject_row_ids_for_dbt_run(
    trino_connection: Any,
    run_results: dict[str, Any],
    catalog: str = "iceberg",
    context: Any = None,
) -> dict[str, dict]:
    """Inject row IDs to all tables from a dbt run.

    Parses dbt run results and injects _phlo_row_id to each
    successfully materialized table.

    Args:
        trino_connection: Trino connection object
        run_results: dbt run_results.json parsed as dict
        catalog: Iceberg catalog name
        context: Optional Dagster context

    Returns:
        Dict mapping table names to injection results
    """
    results = {}

    for result in run_results.get("results", []):
        if result.get("status") != "success":
            continue

        unique_id = result.get("unique_id", "")
        if not unique_id.startswith("model."):
            continue

        # Extract schema and table from unique_id
        # Format: model.project_name.model_name
        parts = unique_id.split(".")
        if len(parts) < 3:
            continue

        model_name = parts[-1]

        # Infer schema from model name
        if model_name.startswith("stg_"):
            schema = "silver"
        elif model_name.startswith(("fct_", "dim_")):
            schema = "gold"
        elif model_name.startswith(("mrt_", "publish_")):
            schema = "marts"
        else:
            schema = "bronze"

        try:
            results[model_name] = inject_row_ids_to_table(
                trino_connection=trino_connection,
                catalog=catalog,
                schema=schema,
                table=model_name,
                context=context,
            )
        except Exception as e:
            results[model_name] = {"error": str(e)}

    return results
