"""Hasura table tracking and auto-discovery."""

import os
import socket
from typing import Any

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from phlo.config import get_settings
from phlo.logging import get_logger
from phlo_hasura.client import HasuraClient

logger = get_logger(__name__)


def _resolve_db_host(host: str, port: int) -> tuple[str, int]:
    """Resolve database host, falling back to localhost if Docker hostname unreachable.

    When running hooks from the host machine, Docker internal hostnames like 'postgres'
    won't resolve. In that case, use localhost with the exposed port.

    Args:
        host: Database host (may be Docker internal hostname)
        port: Database port (may be internal port)

    Returns:
        Tuple of (resolved_host, resolved_port)
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
    """Automatically discovers and tracks PostgreSQL tables in Hasura."""

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
            hasura_client: HasuraClient instance
            db_host: Database host
            db_port: Database port
            db_name: Database name
            db_user: Database user
            db_password: Database password
        """
        self.client = hasura_client or HasuraClient()

        settings = get_settings()
        raw_host = db_host or settings.postgres_host
        raw_port = db_port or settings.postgres_port

        # Resolve host - handle running outside Docker
        self.db_host, self.db_port = _resolve_db_host(raw_host, raw_port)
        self.db_name = db_name or settings.postgres_db
        self.db_user = db_user or settings.postgres_user
        self.db_password = db_password or settings.postgres_password

    def _get_db_connection(self):
        """Get PostgreSQL connection."""
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

        Returns schemas that:
        - Have at least one base table
        - Are not system schemas (pg_*, information_schema, etc.)

        Returns:
            List of schema names
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

        Args:
            schema: Schema name

        Returns:
            List of table names
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

        Args:
            schema: Schema name
            table: Table name

        Returns:
            List of FK information dicts
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

        Args:
            schema: Schema name
            exclude: List of table names to exclude
            verbose: Print progress messages

        Returns:
            Dictionary of table_name -> success
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

        Args:
            schema: Schema name
            verbose: Print progress messages

        Returns:
            Dictionary of (table, relationship) -> success
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

        Args:
            schema: Schema name
            verbose: Print progress messages

        Returns:
            Dictionary of (table, role) -> success
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

    Args:
        schema: Schema name
        verbose: Print progress messages

    Returns:
        Summary of tracking results
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

    Discovers all non-system schemas that contain tables and tracks them in Hasura.

    Args:
        verbose: Print progress messages

    Returns:
        Dict mapping schema names to their tracking results
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
