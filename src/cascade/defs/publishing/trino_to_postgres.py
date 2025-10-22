# trino_to_postgres.py - Publishing asset to move curated marts from Iceberg to PostgreSQL
# Implements the final publishing step of the lakehouse pipeline
# transferring processed analytics data to Postgres for fast BI queries

from __future__ import annotations

import psycopg2
from dagster import AssetKey, asset

from cascade.config import config
from cascade.defs.resources.trino import TrinoResource
from cascade.schemas import PublishPostgresOutput, TablePublishStats


# --- Publishing Asset ---
# Dagster asset that publishes Iceberg marts to PostgreSQL for BI access
@asset(
    name="publish_glucose_marts_to_postgres",
    group_name="publish",
    compute_kind="trino+postgres",
    deps=[
        AssetKey("mrt_glucose_overview"),
        AssetKey("mrt_glucose_hourly_patterns"),
        AssetKey("mrt_github_activity_overview"),
        AssetKey("mrt_github_repo_insights"),
    ],
)
# Publishing function implementation
def publish_glucose_marts_to_postgres(
    context, trino: TrinoResource
) -> PublishPostgresOutput:
    """
    Publish curated marts from Iceberg (via Trino) to Postgres for BI/Superset.

    Strategy:
    1. Query mart tables from Iceberg via Trino
    2. Write results to Postgres using COPY for performance
    3. Postgres tables serve as fast query layer for Superset dashboards

    Source: Iceberg bronze/silver/gold/marts schemas
    Target: Postgres marts schema
    """
    # Configuration setup
    target_schema = config.postgres_mart_schema

    # --- Table Configuration ---
    # Tables to publish from Iceberg to Postgres
    tables_to_publish = {
        "mrt_glucose_overview": "iceberg.marts.mrt_glucose_overview",
        "mrt_glucose_hourly_patterns": "iceberg.marts.mrt_glucose_hourly_patterns",
        "mrt_github_activity_overview": "iceberg.marts.mrt_github_activity_overview",
        "mrt_github_repo_insights": "iceberg.marts.mrt_github_repo_insights",
    }

    context.log.info(
        "Publishing Iceberg marts to Postgres via Trino. target_schema=%s",
        target_schema,
    )

    # --- Database Connection ---
    # Connect to Postgres
    pg_conn = psycopg2.connect(
        host=config.postgres_host,
        port=config.postgres_port,
        user=config.postgres_user,
        password=config.postgres_password,
        dbname=config.postgres_db,
    )
    pg_conn.autocommit = False

    table_stats: dict[str, TablePublishStats] = {}

    try:
        pg_cursor = pg_conn.cursor()

        # Ensure target schema exists
        pg_cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{target_schema}"')
        pg_conn.commit()

        for table_alias, iceberg_table in tables_to_publish.items():
            context.log.info(
                "Publishing table %s from Iceberg source %s",
                f"{target_schema}.{table_alias}",
                iceberg_table,
            )

            # Drop existing Postgres table
            pg_cursor.execute(
                f'DROP TABLE IF EXISTS "{target_schema}"."{table_alias}" CASCADE'
            )
            pg_conn.commit()

            # Query Iceberg table via Trino
            with trino.cursor(schema="marts") as trino_cursor:
                trino_cursor.execute(f"SELECT * FROM {iceberg_table}")

                # Get column names
                columns = [desc[0] for desc in trino_cursor.description]
                column_list = ", ".join(f'"{col}"' for col in columns)

                # Fetch all rows (for small mart tables this is fine)
                rows = trino_cursor.fetchall()
            row_count = len(rows)

            if row_count == 0:
                context.log.warning(
                    "No data in source table %s, skipping", iceberg_table
                )
                continue

            # Infer Postgres types from first row and Trino metadata
            # For simplicity, use TEXT for all columns (Postgres will handle it)
            # In production, you'd want proper type mapping
            col_defs = ", ".join(f'"{col}" TEXT' for col in columns)

            # Create Postgres table
            create_sql = (
                f'CREATE TABLE "{target_schema}"."{table_alias}" ({col_defs})'
            )
            pg_cursor.execute(create_sql)

            # Insert data in batches using executemany for performance
            insert_sql = f'INSERT INTO "{target_schema}"."{table_alias}" ({column_list}) VALUES ({", ".join(["%s"] * len(columns))})'

            # Convert rows to proper format (handle None values)
            formatted_rows = []
            for row in rows:
                formatted_row = tuple(
                    str(val) if val is not None else None for val in row
                )
                formatted_rows.append(formatted_row)

            pg_cursor.executemany(insert_sql, formatted_rows)
            pg_conn.commit()

            table_stats[table_alias] = TablePublishStats(
                row_count=row_count,
                column_count=len(columns),
            )

            context.log.info(
                "Published table %s with %d rows, %d columns",
                f"{target_schema}.{table_alias}",
                row_count,
                len(columns),
            )

    except Exception as exc:
        pg_conn.rollback()
        context.log.exception(
            "Failed to publish Iceberg marts to Postgres: %s",
            exc,
        )
        raise RuntimeError(
            f"Failed to publish marts to Postgres schema '{target_schema}'. "
            "Check Trino/Postgres connectivity and source tables."
        ) from exc
    finally:
        pg_conn.close()

    output = PublishPostgresOutput(tables=table_stats)
    context.add_output_metadata(output.model_dump())
    return output
