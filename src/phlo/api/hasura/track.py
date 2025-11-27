"""Hasura table tracking and auto-discovery."""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from phlo.api.hasura.client import HasuraClient
from phlo.config import get_settings


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
        self.db_host = db_host or settings.postgres_host
        self.db_port = db_port or settings.postgres_port
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
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))

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
            cursor.execute("""
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
            """, (schema, table))

            fks = []
            for local_col, ref_schema, ref_table, ref_col in cursor.fetchall():
                fks.append({
                    "local_column": local_col,
                    "ref_schema": ref_schema,
                    "ref_table": ref_table,
                    "ref_column": ref_col,
                })

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
            print(f"Discovering tables in schema '{schema}'...")

        tables = self.get_tables_in_schema(schema)
        exclude = exclude or []
        tables = [t for t in tables if t not in exclude]

        if verbose:
            print(f"Found {len(tables)} tables")
            print()

        results = {}
        for table in tables:
            try:
                if verbose:
                    print(f"Tracking {schema}.{table}...", end=" ")

                self.client.track_table(schema, table)
                results[table] = True

                if verbose:
                    print("✓")
            except Exception as e:
                results[table] = False
                if verbose:
                    print(f"✗ ({str(e)[:50]})")

        return results

    def setup_relationships(
        self, schema: str, verbose: bool = True
    ) -> dict[tuple[str, str], bool]:
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
                        print(
                            f"Creating relationship {table}.{rel_name} "
                            f"-> {fk['ref_table']}...",
                            end=" ",
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
                        print("✓")
                except Exception as e:
                    results[(table, rel_name)] = False
                    if verbose:
                        print(f"✗ ({str(e)[:50]})")

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
                        print(
                            f"Creating permission {table}.{role}...", end=" "
                        )

                    self.client.create_select_permission(
                        schema, table, role, filter=filter_expr
                    )

                    results[(table, role)] = True
                    if verbose:
                        print("✓")
                except Exception as e:
                    results[(table, role)] = False
                    if verbose:
                        print(f"✗ ({str(e)[:50]})")

        return results


def auto_track(schema: str = "api", verbose: bool = True) -> dict[str, any]:
    """Convenience function to auto-track all tables in a schema.

    Args:
        schema: Schema name
        verbose: Print progress messages

    Returns:
        Summary of tracking results
    """
    if verbose:
        print("=" * 60)
        print("Hasura Auto-Track")
        print("=" * 60)
        print()

    tracker = HasuraTableTracker()

    # Track tables
    track_results = tracker.track_tables(schema, verbose=verbose)
    if verbose:
        print()

    # Setup relationships
    print("Setting up relationships...")
    rel_results = tracker.setup_relationships(schema, verbose=verbose)
    if verbose:
        print()

    # Setup default permissions
    print("Setting up default permissions...")
    perm_results = tracker.setup_default_permissions(schema, verbose=verbose)

    if verbose:
        print()
        print("=" * 60)
        print("✓ Auto-track completed")
        print(f"  Tables tracked: {sum(1 for v in track_results.values() if v)}/{len(track_results)}")
        print(f"  Relationships: {sum(1 for v in rel_results.values() if v)}/{len(rel_results)}")
        print(f"  Permissions: {sum(1 for v in perm_results.values() if v)}/{len(perm_results)}")
        print("=" * 60)

    return {
        "tables": track_results,
        "relationships": rel_results,
        "permissions": perm_results,
    }
