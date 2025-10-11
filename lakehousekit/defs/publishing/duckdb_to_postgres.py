from __future__ import annotations

import os
from urllib.parse import quote_plus

import duckdb
from dagster import AssetKey, asset


@asset(
    name="publish_glucose_marts_to_postgres",
    group_name="publish",
    compute_kind="postgres",
    deps=[
        AssetKey("mart_glucose_overview"),
        AssetKey("mart_glucose_hourly_patterns"),
        AssetKey("fact_glucose_readings"),
    ],
)
def publish_glucose_marts_to_postgres(context) -> dict[str, dict[str, int]]:
    duckdb_path = os.getenv("DUCKDB_WAREHOUSE_PATH", "/data/duckdb/warehouse.duckdb")
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user = os.getenv("POSTGRES_USER", "lake")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "lakepass")
    postgres_db = os.getenv("POSTGRES_DB", "lakehouse")
    target_schema = os.getenv("POSTGRES_MART_SCHEMA", "marts")

    tables_to_publish = {
        "mart_glucose_overview": "main_marts.mart_glucose_overview",
        "mart_glucose_hourly_patterns": "main_marts.mart_glucose_hourly_patterns",
        "fact_glucose_readings": "main_curated.fact_glucose_readings",
    }

    context.log.info(
        "Publishing DuckDB marts to Postgres. duckdb_path=%s target_schema=%s",
        duckdb_path,
        target_schema,
    )

    password_escaped = quote_plus(postgres_password)
    user_escaped = quote_plus(postgres_user)
    host_escaped = quote_plus(postgres_host)
    dsn = (
        f"postgres://{user_escaped}:{password_escaped}@{host_escaped}:{postgres_port}/{postgres_db}"
    )

    success_counts: dict[str, dict[str, int]] = {}
    with duckdb.connect(database=duckdb_path, read_only=False) as duck_con:
        duck_con.execute("INSTALL postgres")
        duck_con.execute("LOAD postgres")
        duck_con.execute(f"ATTACH '{dsn}' AS pg_marts (TYPE POSTGRES, READ_ONLY FALSE)")
        duck_con.execute(f'CREATE SCHEMA IF NOT EXISTS pg_marts."{target_schema}"')

        for table_alias, duck_table in tables_to_publish.items():
            context.log.info(
                "Replacing Postgres table %s from DuckDB source %s",
                f"{target_schema}.{table_alias}",
                duck_table,
            )
            duck_con.execute(
                f'DROP TABLE IF EXISTS pg_marts."{target_schema}"."{table_alias}" CASCADE'
            )
            duck_con.execute(
                f'CREATE TABLE pg_marts."{target_schema}"."{table_alias}" AS SELECT * FROM {duck_table}'
            )

            row_count = duck_con.execute(
                f'SELECT COUNT(*) FROM pg_marts."{target_schema}"."{table_alias}"'
            ).fetchone()[0]
            column_count = duck_con.execute(
                """
                SELECT COUNT(*)
                FROM pg_marts.information_schema.columns
                WHERE table_schema = ?
                  AND table_name = ?
                """,
                [target_schema, table_alias],
            ).fetchone()[0]

            success_counts[table_alias] = {
                "row_count": row_count,
                "column_count": column_count,
            }
            context.log.info(
                "Published table %s with %d rows",
                f"{target_schema}.{table_alias}",
                row_count,
            )

        duck_con.execute("DETACH pg_marts")

    context.add_output_metadata(success_counts)
    return success_counts
