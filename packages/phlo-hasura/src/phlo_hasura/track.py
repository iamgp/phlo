"""Hasura table tracking and auto-discovery.

This module provides classes and functions for automatically discovering
and tracking PostgreSQL tables in Hasura. It handles schema discovery,
foreign key relationship detection, and bulk table operations.

Classes:
    HasuraPostgresSettings: PostgreSQL connection settings.
    HasuraTableTracker: Automatically discovers and tracks tables.

Functions:
    auto_track: Convenience function to auto-track all tables in a schema.
    auto_track_all: Auto-discover and track all tables in all user schemas.
    _resolve_db_host: Resolve database host with Docker hostname handling.

Example:
    >>> from phlo_hasura.track import HasuraTableTracker, auto_track
    >>> tracker = HasuraTableTracker()
    >>> tracker.track_tables("api")
    >>> auto_track("api")

"""

import os
import socket
from typing import Any

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from phlo.config.base import BaseConfig
from phlo.logging import get_logger
from phlo_hasura.client import HasuraClient
from pydantic import Field

logger = get_logger(__name__)


class HasuraPostgresSettings(BaseConfig):
    """PostgreSQL connection settings used by Hasura table tracking.

        Pydantic model for PostgreSQL connection configuration with sensible
    defaults for Docker environments.

    Attributes:
            postgres_host: PostgreSQL server hostname (default: "postgres").
            postgres_port: PostgreSQL server port (default: 5432).
            postgres_user: Database username (default: "phlo").
            postgres_password: Database password (default: "phlo").
            postgres_db: Database name (default: "phlo").

    Example:
            >>> settings = HasuraPostgresSettings()
            >>> print(f"Connecting to {settings.postgres_host}:{settings.postgres_port}")
            Connecting to postgres:5432
            >>> custom = HasuraPostgresSettings(postgres_host="localhost")

    """

    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="phlo", description="PostgreSQL username")
    postgres_password: str = Field(default="phlo", description="PostgreSQL password")
    postgres_db: str = Field(default="phlo", description="PostgreSQL database name")


def _resolve_db_host(host: str, port: int) -> tuple[str, int]:
    """Resolve database host, falling back to localhost if Docker hostname unreachable.

    When running hooks from the host machine, Docker internal hostnames like 'postgres'
    won't resolve. In that case, use localhost with the exposed port.

    Args:
        host: Database host (may be Docker internal hostname like 'postgres').
        port: Database port (may be internal port).

    Returns:
        Tuple of (resolved_host, resolved_port) suitable for connection.
        If Docker hostname fails to resolve, returns ('localhost', POSTGRES_PORT).

    Example:
        >>> host, port = _resolve_db_host("postgres", 5432)
        >>> # If running outside Docker:
        >>> # host = "localhost", port = 5432 (or from POSTGRES_PORT env)

    """
    # If already localhost, use as-is
    if host in ("localhost", "127.0.0.1"):
        return host, port

    # Try to resolve the hostname
    try:
        socket.gethostbyname(host)
        return host, port
    except socket.gaierror:
        # Can't resolve - we're likely running on the host, not in Docker
        # Use localhost with the exposed port from environment
        exposed_port = int(os.environ.get("POSTGRES_PORT", port))
        logger.debug(
            "Cannot resolve '%s', using localhost:%s (running outside Docker)",
            host,
            exposed_port,
        )
        return "localhost", exposed_port


class HasuraTableTracker:
    """Automatically discovers and tracks PostgreSQL tables in Hasura.

    Provides methods for schema discovery, table tracking, relationship
    creation from foreign keys, and default permission setup.

    Attributes:
        client: HasuraClient for Hasura API operations.
        db_host: Resolved PostgreSQL host.
        db_port: Resolved PostgreSQL port.
        db_name: PostgreSQL database name.
        db_user: PostgreSQL username.
        db_password: PostgreSQL password.

    Example:
        >>> tracker = HasuraTableTracker()
        >>> schemas = tracker.discover_user_schemas()
        >>> results = tracker.track_tables("api")
        >>> tracker.setup_relationships("api")

    """

    def __init__(
        self,
        hasura_client: HasuraClient | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_user: str | None = None,
        db_password: str | None = None,
    ):
        """Initialize table tracker.

        Args:
            hasura_client: HasuraClient instance for API operations.
            db_host: PostgreSQL host (default: from HasuraPostgresSettings).
            db_port: PostgreSQL port (default: from HasuraPostgresSettings).
            db_name: PostgreSQL database name (default: from HasuraPostgresSettings).
            db_user: PostgreSQL username (default: from HasuraPostgresSettings).
            db_password: PostgreSQL password (default: from HasuraPostgresSettings).

        The database host is automatically resolved to handle running
        outside Docker containers.

        Example:
            >>> tracker = HasuraTableTracker()
            >>> custom_tracker = HasuraTableTracker(
            ...     db_host="localhost",
            ...     db_port=5433
            ... )

        """
        self.client = hasura_client or HasuraClient()

        settings = HasuraPostgresSettings()
        raw_host = db_host or settings.postgres_host
        raw_port = db_port or settings.postgres_port

        # Resolve host - handle running outside Docker
        self.db_host, self.db_port = _resolve_db_host(raw_host, raw_port)
        self.db_name = db_name or settings.postgres_db
        self.db_user = db_user or settings.postgres_user
        self.db_password = db_password or settings.postgres_password

    def _get_db_connection(self):
        """Get PostgreSQL database connection.

        Creates and returns a psycopg2 connection with autocommit enabled.
        The connection is configured with the resolved host and port.

        Returns:
            psycopg2 connection object with ISOLATION_LEVEL_AUTOCOMMIT.

        Raises:
            psycopg2.Error: If connection fails.

        Example:
            >>> conn = tracker._get_db_connection()
            >>> cursor = conn.cursor()
            >>> cursor.execute("SELECT version()")

        """
        conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    def discover_user_schemas(self) -> list[str]:
        """Discover all user schemas that contain tables.

        Queries the database to find all schemas that:
        - Have at least one base table
        - Are not system schemas (pg_*, information_schema, etc.)

        Returns:
            Sorted list of schema names containing user tables.

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> schemas = tracker.discover_user_schemas()
            >>> print(schemas)
            ['api', 'marts', 'public']

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT DISTINCT table_schema
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema NOT LIKE 'pg_%%'
                  AND table_schema != 'information_schema'
                ORDER BY table_schema
                """
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def get_tables_in_schema(self, schema: str) -> list[str]:
        """Get all tables in a schema.

        Queries the information_schema to find all base tables
        within the specified database schema.

        Args:
            schema: Schema name to query.

        Returns:
            Sorted list of table names in the schema.

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> tables = tracker.get_tables_in_schema("api")
            >>> print(tables)
            ['customers', 'orders', 'products']

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """,
                (schema,),
            )

            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def get_foreign_keys(self, schema: str, table: str) -> list[dict]:
        """Get foreign key constraints for a table.

        Queries the information_schema to find all foreign key
        relationships defined on the specified table.

        Args:
            schema: Schema name containing the table.
            table: Table name to query for foreign keys.

        Returns:
            List of foreign key dictionaries with keys:
                - local_column: Column in the source table
                - ref_schema: Schema of referenced table
                - ref_table: Name of referenced table
                - ref_column: Column in referenced table

        Raises:
            psycopg2.Error: If database query fails.

        Example:
            >>> fks = tracker.get_foreign_keys("api", "orders")
            >>> for fk in fks:
            ...     print(f"{fk['local_column']} -> {fk['ref_table']}.{fk['ref_column']}")
            customer_id -> customers.id

        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    kcu.column_name,
                    ccu.table_schema,
                    ccu.table_name,
                    ccu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ORDER BY kcu.column_name
            """,
                (schema, table),
            )

            fks = []
            for local_col, ref_schema, ref_table, ref_col in cursor.fetchall():
                fks.append(
                    {
                        "local_column": local_col,
                        "ref_schema": ref_schema,
                        "ref_table": ref_table,
                        "ref_column": ref_col,
                    }
                )

            return fks
        finally:
            cursor.close()
            conn.close()

    def track_tables(
        self, schema: str, exclude: list[str] | None = None, verbose: bool = True
    ) -> dict[str, bool]:
        """Track all tables in a schema.

        Discovers all tables in the specified schema and tracks them
        in Hasura, optionally excluding specific tables.

        Args:
            schema: Schema name to track tables from.
            exclude: List of table names to skip (default: None).
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping table_name -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.track_tables("api")
            >>> print(f"Tracked {sum(results.values())}/{len(results)} tables")
            >>> results = tracker.track_tables("api", exclude=["temp_table"])

        """
        if verbose:
            logger.info("Discovering tables in schema '%s'...", schema)

        tables = self.get_tables_in_schema(schema)
        exclude = exclude or []
        tables = [t for t in tables if t not in exclude]

        if verbose:
            logger.info("Found %s tables", len(tables))

        results = {}
        for table in tables:
            try:
                if verbose:
                    logger.info("Tracking %s.%s...", schema, table)

                self.client.track_table(schema, table)
                results[table] = True

                if verbose:
                    logger.info("Tracking %s.%s ✓", schema, table)
            except Exception as e:
                results[table] = False
                if verbose:
                    logger.warning("Tracking %s.%s ✗ (%s)", schema, table, str(e)[:200])

        return results

    def setup_relationships(self, schema: str, verbose: bool = True) -> dict[tuple[str, str], bool]:
        """Auto-create relationships from foreign keys.

        Discovers foreign key constraints in all tables of the schema
        and creates corresponding object relationships in Hasura.

        Relationship names are derived from the local column name by
        removing '_id' suffix (e.g., 'customer_id' -> 'customer').

        Args:
            schema: Schema name to set up relationships in.
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping (table, relationship_name) -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.setup_relationships("api")
            >>> for (table, rel), success in results.items():
            ...     status = "created" if success else "failed"
            ...     print(f"{table}.{rel}: {status}")

        """
        tables = self.get_tables_in_schema(schema)
        results = {}

        for table in tables:
            fks = self.get_foreign_keys(schema, table)

            for fk in fks:
                rel_name = fk["local_column"].replace("_id", "")

                try:
                    if verbose:
                        logger.info(
                            "Creating relationship %s.%s -> %s...",
                            table,
                            rel_name,
                            fk["ref_table"],
                        )

                    self.client.create_object_relationship(
                        schema,
                        table,
                        rel_name,
                        manual_configuration={
                            "foreign_key_constraint_on": fk["local_column"],
                        },
                    )

                    results[(table, rel_name)] = True
                    if verbose:
                        logger.info("Creating relationship %s.%s ✓", table, rel_name)
                except Exception as e:
                    results[(table, rel_name)] = False
                    if verbose:
                        logger.warning(
                            "Creating relationship %s.%s ✗ (%s)", table, rel_name, str(e)[:200]
                        )

        return results

    def setup_default_permissions(
        self, schema: str, verbose: bool = True
    ) -> dict[tuple[str, str], bool]:
        """Set up default permissions for tables.

        Creates default SELECT permissions for standard roles (anon, analyst, admin)
        on all tables in the specified schema. The 'anon' role gets full access,
        while 'analyst' and 'admin' get standard access.

        Args:
            schema: Schema name to set up permissions in.
            verbose: Print progress messages (default: True).

        Returns:
            Dictionary mapping (table, role) -> success boolean.

        Raises:
            requests.RequestException: If Hasura API calls fail.
            psycopg2.Error: If database queries fail.

        Example:
            >>> results = tracker.setup_default_permissions("api")
            >>> print(f"Created {sum(results.values())} permissions")

        """
        tables = self.get_tables_in_schema(schema)
        results = {}

        # Default: allow anon users to view api schema
        default_permissions = [
            ("anon", {"allow_aggregations": True}),
            ("analyst", {}),
            ("admin", {}),
        ]

        for table in tables:
            for role, filter_expr in default_permissions:
                try:
                    if verbose:
                        logger.info("Creating permission %s.%s...", table, role)

                    self.client.create_select_permission(schema, table, role, filter=filter_expr)

                    results[(table, role)] = True
                    if verbose:
                        logger.info("Creating permission %s.%s ✓", table, role)
                except Exception as e:
                    results[(table, role)] = False
                    if verbose:
                        logger.warning(
                            "Creating permission %s.%s ✗ (%s)", table, role, str(e)[:200]
                        )

        return results


def auto_track(schema: str = "api", verbose: bool = True) -> dict[str, Any]:
    """Convenience function to auto-track all tables in a schema.

    Performs complete auto-configuration of a schema: tracks all tables,
    creates relationships from foreign keys, and sets up default permissions.

    Args:
        schema: Schema name to auto-configure (default: "api").
        verbose: Print progress messages (default: True).

    Returns:
        Dictionary containing tracking results:
        {
            "tables": {table_name: success_bool, ...},
            "relationships": {(table, rel): success_bool, ...},
            "permissions": {(table, role): success_bool, ...}
        }

    Raises:
        requests.RequestException: If Hasura API calls fail.
        psycopg2.Error: If database queries fail.

    Example:
        >>> results = auto_track("api")
        >>> print(f"Tables: {sum(results['tables'].values())}/{len(results['tables'])}")

    """
    if verbose:
        logger.info("=" * 60)
        logger.info("Hasura Auto-Track")
        logger.info("=" * 60)

    tracker = HasuraTableTracker()

    # Track tables
    track_results = tracker.track_tables(schema, verbose=verbose)
    if verbose:
        logger.info("")

    # Setup relationships
    if verbose:
        logger.info("Setting up relationships...")
    rel_results = tracker.setup_relationships(schema, verbose=verbose)
    if verbose:
        logger.info("")

    # Setup default permissions
    if verbose:
        logger.info("Setting up default permissions...")
    perm_results = tracker.setup_default_permissions(schema, verbose=verbose)

    if verbose:
        logger.info("=" * 60)
        logger.info("✓ Auto-track completed")
        logger.info(
            "  Tables tracked: %s/%s",
            sum(1 for v in track_results.values() if v),
            len(track_results),
        )
        logger.info(
            "  Relationships: %s/%s",
            sum(1 for v in rel_results.values() if v),
            len(rel_results),
        )
        logger.info(
            "  Permissions: %s/%s",
            sum(1 for v in perm_results.values() if v),
            len(perm_results),
        )
        logger.info("=" * 60)

    return {
        "tables": track_results,
        "relationships": rel_results,
        "permissions": perm_results,
    }


def auto_track_all(verbose: bool = True) -> dict[str, dict[str, Any]]:
    """Auto-discover and track all tables in all user schemas.

    Discovers all non-system schemas containing tables and runs
    auto_track() on each one.

    Args:
        verbose: Print progress messages (default: True).

    Returns:
        Dictionary mapping schema_name -> tracking results dict.
        Each schema's results contains tables, relationships, and permissions.

    Raises:
        requests.RequestException: If Hasura API calls fail.
        psycopg2.Error: If database queries fail.

    Example:
        >>> all_results = auto_track_all()
        >>> for schema, results in all_results.items():
        ...     tracked = sum(results['tables'].values())
        ...     print(f"{schema}: {tracked} tables tracked")

    """
    if verbose:
        logger.info("=" * 60)
        logger.info("Hasura Auto-Track (All Schemas)")
        logger.info("=" * 60)

    tracker = HasuraTableTracker()
    schemas = tracker.discover_user_schemas()

    if verbose:
        logger.info("Discovered %d user schemas: %s", len(schemas), ", ".join(schemas))
        logger.info("")

    results: dict[str, dict[str, Any]] = {}
    for schema in schemas:
        if verbose:
            logger.info("Processing schema: %s", schema)
        results[schema] = auto_track(schema=schema, verbose=verbose)

    if verbose:
        logger.info("=" * 60)
        logger.info("✓ All schemas processed")
        total_tables = sum(len(r.get("tables", {})) for r in results.values())
        tracked_tables = sum(
            sum(1 for v in r.get("tables", {}).values() if v) for r in results.values()
        )
        logger.info("  Total tables tracked: %d/%d", tracked_tables, total_tables)
        logger.info("=" * 60)

    return results
