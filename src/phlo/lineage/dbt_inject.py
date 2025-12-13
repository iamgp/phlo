from __future__ import annotations

from typing import Any


def inject_row_ids_to_table(
    *,
    trino_connection: Any,
    catalog: str,
    schema: str,
    table: str,
    context: Any | None = None,
) -> dict[str, Any]:
    cursor = trino_connection.cursor()

    fqtn = f"{catalog}.{schema}.{table}"

    cursor.execute(f"DESCRIBE {fqtn}")
    column_rows = cursor.fetchall()
    column_names = {row[0] for row in column_rows}

    if "_phlo_row_id" in column_names:
        return {"rows_updated": 0, "skipped": True}

    if context is not None:
        context.log.info(f"Injecting _phlo_row_id into {fqtn}")

    cursor.execute(f"ALTER TABLE {fqtn} ADD COLUMN _phlo_row_id VARCHAR")

    cursor.execute(f"SELECT COUNT(*) FROM {fqtn}")
    (row_count,) = cursor.fetchone()

    cursor.execute(
        f"UPDATE {fqtn} SET _phlo_row_id = CAST(uuid() AS VARCHAR) WHERE _phlo_row_id IS NULL"
    )

    return {"rows_updated": int(row_count)}


def inject_row_ids_for_dbt_run(
    *,
    trino_connection: Any,
    run_results: dict[str, Any],
    catalog: str = "iceberg",
    context: Any | None = None,
) -> dict[str, Any]:
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
