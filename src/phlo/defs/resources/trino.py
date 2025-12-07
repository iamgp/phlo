# trino.py - Dagster resource for Trino SQL query execution with Iceberg integration
# Provides convenient helpers for executing SQL queries against Iceberg tables
# via Trino, with branch-aware catalog selection for dev/prod isolation
#
# Nessie Branching Architecture:
# -----------------------------
# Nessie branching in Trino requires separate catalogs per branch because
# the branch is configured via `iceberg.rest-catalog.prefix` in catalog properties.
#
# Catalog Setup:
#   - iceberg.properties       -> prefix=main  (production data)
#   - iceberg_dev.properties   -> prefix=dev   (development/feature branches)
#
# Write-Audit-Publish Pattern:
#   1. Ingestion writes to feature branch (via PyIceberg, supports dynamic branches)
#   2. dbt transforms run on feature branch (use iceberg_dev catalog)
#   3. Quality checks validate on feature branch
#   4. On validation pass -> Nessie merge to main
#   5. Publishing copies from main (iceberg catalog) to Postgres for BI

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Literal, Sequence

from dagster import ConfigurableResource
from trino.dbapi import Connection, Cursor, connect

from phlo.config import config

# Catalog names for different branches
CATALOG_MAIN = "iceberg"  # Points to Nessie main branch
CATALOG_DEV = "iceberg_dev"  # Points to Nessie dev branch


class TrinoResource(ConfigurableResource):
    """
    Dagster resource for Trino SQL execution with Iceberg/Nessie integration.

    Supports branch-aware queries through catalog selection:
    - `catalog="iceberg"` -> main branch (production)
    - `catalog="iceberg_dev"` -> dev branch (feature work)

    Example:
        ```python
        # Read from main branch (production)
        trino = TrinoResource()
        rows = trino.execute("SELECT * FROM iceberg.marts.my_table")

        # Read from dev branch
        trino_dev = TrinoResource(catalog="iceberg_dev")
        rows = trino_dev.execute("SELECT * FROM iceberg_dev.staging.my_table")
        ```
    """

    host: str = config.trino_host
    port: int = config.trino_port
    user: str = "dagster"
    catalog: str = config.trino_catalog
    trino_schema: str | None = None

    def get_connection(
        self, schema: str | None = None, branch: Literal["main", "dev"] | None = None
    ) -> Connection:
        """
        Open a Trino DB-API connection.

        Args:
            schema: Schema to use for queries
            branch: Branch to use ("main" or "dev"). If specified, overrides
                    the default catalog to use the branch-specific catalog.
        """
        # Select catalog based on branch
        catalog = self.catalog
        if branch == "main":
            catalog = CATALOG_MAIN
        elif branch == "dev":
            catalog = CATALOG_DEV

        return connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=catalog,
            schema=schema or self.trino_schema,
        )

    @contextmanager
    def connection(
        self, schema: str | None = None, branch: Literal["main", "dev"] | None = None
    ) -> Iterator[Connection]:
        """
        Context manager that yields a Trino connection and ensures it gets closed.

        Args:
            schema: Schema to use for queries
            branch: Branch to use ("main" or "dev")
        """
        conn = self.get_connection(schema=schema, branch=branch)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def cursor(
        self, schema: str | None = None, branch: Literal["main", "dev"] | None = None
    ) -> Iterator[Cursor]:
        """
        Context manager for a Trino cursor, closing both cursor and connection.

        Args:
            schema: Schema to use for queries
            branch: Branch to use ("main" or "dev")
        """
        with self.connection(schema=schema, branch=branch) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute(
        self,
        sql: str,
        parameters: Sequence[Any] | None = None,
        schema: str | None = None,
        branch: Literal["main", "dev"] | None = None,
    ) -> list[tuple[Any, ...]]:
        """
        Execute SQL and fetch all rows.

        Args:
            sql: SQL query to execute
            parameters: Optional query parameters
            schema: Schema to use for queries
            branch: Branch to use ("main" or "dev")

        Returns:
            List of result tuples, or empty list for statements without a result set
        """
        with self.cursor(schema=schema, branch=branch) as cursor:
            cursor.execute(sql, parameters or [])
            if cursor.description:
                return cursor.fetchall()
            return []
