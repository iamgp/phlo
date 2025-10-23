# trino_to_postgres.py - Publishing asset factory to move curated marts from Iceberg to PostgreSQL
# Implements the final publishing step of the lakehouse pipeline
# transferring processed analytics data to Postgres for fast BI queries

from __future__ import annotations

import psycopg2
import yaml
from dagster import AssetKey, asset
from pathlib import Path

from cascade.config import config
from cascade.defs.resources.trino import TrinoResource
from cascade.schemas import PublishPostgresOutput, TablePublishStats


# --- Shared Publishing Logic ---
# Generic function for publishing Iceberg marts to PostgreSQL
def _publish_marts_to_postgres(
    context,
    trino: TrinoResource,
    tables_to_publish: dict[str, str],
    data_source: str,
) -> PublishPostgresOutput:
    """
    Generic function to publish curated marts from Iceberg (via Trino) to Postgres.

    Args:
        context: Dagster asset execution context
        trino: Trino resource for querying Iceberg
        tables_to_publish: Dict mapping Postgres table names to Iceberg table paths
        data_source: Description of data source for logging (e.g., "glucose", "GitHub")

    Returns:
        PublishPostgresOutput with table statistics
    """
    # Configuration setup
    target_schema = config.postgres_mart_schema

    context.log.info(
        f"Publishing {data_source} Iceberg marts to Postgres via Trino. target_schema=%s",
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
                f"Publishing {data_source} table %s from Iceberg source %s",
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
                f"Published {data_source} table %s with %d rows, %d columns",
                f"{target_schema}.{table_alias}",
                row_count,
                len(columns),
            )

    except Exception as exc:
        pg_conn.rollback()
        context.log.exception(
            f"Failed to publish {data_source} Iceberg marts to Postgres: %s",
            exc,
        )
        raise RuntimeError(
            f"Failed to publish {data_source} marts to Postgres schema '{target_schema}'. "
            "Check Trino/Postgres connectivity and source tables."
        ) from exc
    finally:
        pg_conn.close()

    output = PublishPostgresOutput(tables=table_stats)
    context.add_output_metadata(output.model_dump())
    return output


# --- Asset Factory ---
# Dynamically create publishing assets from YAML configuration

def create_publishing_assets():
    """
    Factory function that reads publishing config from YAML and creates assets dynamically.

    Returns:
        List of dynamically created Dagster assets
    """
    # Load configuration from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    assets = []

    for data_source, config_item in config_data['publishing'].items():
        # Create asset dynamically
        asset_name = config_item['name']
        group_name = config_item['group']
        description = config_item['description']
        dependencies = [AssetKey(dep) for dep in config_item['dependencies']]
        tables_to_publish = config_item['tables']

        @asset(
            name=asset_name,
            group_name=group_name,
            compute_kind="trino+postgres",
            deps=dependencies,
        )
        def publishing_asset(context, trino: TrinoResource) -> PublishPostgresOutput:
            return _publish_marts_to_postgres(
                context=context,
                trino=trino,
                tables_to_publish=tables_to_publish,
                data_source=data_source.capitalize()
            )

        # Set the docstring dynamically
        publishing_asset.__doc__ = f"""
        {description}

        Source: Iceberg marts schema ({data_source} data)
        Target: Postgres marts schema

        Tables: {', '.join(tables_to_publish.keys())}
        """

        # Rename the function to avoid conflicts
        publishing_asset.__name__ = asset_name

        assets.append(publishing_asset)

    return assets


# Create the assets
PUBLISHING_ASSETS = create_publishing_assets()
