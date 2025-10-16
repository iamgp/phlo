from __future__ import annotations

from urllib.parse import quote_plus

from dagster import AssetKey, asset

from lakehousekit.config import config
from lakehousekit.defs.resources import DuckLakeResource
from lakehousekit.schemas import PublishPostgresOutput, TablePublishStats


@asset(
    name="publish_glucose_marts_to_postgres",
    group_name="publish",
    compute_kind="postgres",
    deps=[
        AssetKey("mrt_glucose_overview"),
        AssetKey("mrt_glucose_hourly_patterns"),
    ],
)
def publish_glucose_marts_to_postgres(context, duckdb: DuckLakeResource) -> PublishPostgresOutput:
    ducklake_path = config.ducklake_data_path
    postgres_host = config.postgres_host
    postgres_port = config.postgres_port
    postgres_user = config.postgres_user
    postgres_password = config.postgres_password
    postgres_db = config.postgres_db
    target_schema = config.postgres_mart_schema
    catalog_alias = config.ducklake_catalog_alias

    tables_to_publish = {
        "mrt_glucose_overview": f"{catalog_alias}.main_marts.mrt_glucose_overview",
        "mrt_glucose_hourly_patterns": f"{catalog_alias}.main_marts.mrt_glucose_hourly_patterns",
    }

    context.log.info(
        "Publishing DuckLake marts to Postgres. data_path=%s target_schema=%s",
        ducklake_path,
        target_schema,
    )

    password_escaped = quote_plus(postgres_password)
    user_escaped = quote_plus(postgres_user)
    host_escaped = quote_plus(postgres_host)
    dsn = (
        f"postgres://{user_escaped}:{password_escaped}@{host_escaped}:{postgres_port}/{postgres_db}"
    )

    table_stats: dict[str, TablePublishStats] = {}
    try:
        with duckdb.get_connection() as duck_con:
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
                create_table_sql = (
                    f'CREATE TABLE pg_marts."{target_schema}"."{table_alias}" '
                    f"AS SELECT * FROM {duck_table}"
                )
                duck_con.execute(create_table_sql)

                row_count_result = duck_con.execute(
                f'SELECT COUNT(*) FROM pg_marts."{target_schema}"."{table_alias}"'
                ).fetchone()
                row_count = row_count_result[0] if row_count_result else 0
                column_count = duck_con.execute(
                    """
                    SELECT COUNT(*)
                    FROM pg_marts.information_schema.columns
                    WHERE table_schema = ?
                      AND table_name = ?
                    """,
                    [target_schema, table_alias],
                ).fetchone()[0]

                table_stats[table_alias] = TablePublishStats(
                    row_count=row_count,
                    column_count=column_count,
                )
                context.log.info(
                    "Published table %s with %d rows",
                    f"{target_schema}.{table_alias}",
                    row_count,
                )

            duck_con.execute("DETACH pg_marts")
    except Exception as exc:
        context.log.exception(
            "Failed to publish DuckLake marts to Postgres: %s",
            exc,
        )
        raise RuntimeError(
            f"Failed to publish marts to Postgres schema '{target_schema}'. "
            "Check database connectivity and DuckDB source tables."
        ) from exc

    output = PublishPostgresOutput(tables=table_stats)
    context.add_output_metadata(output.model_dump())
    return output
