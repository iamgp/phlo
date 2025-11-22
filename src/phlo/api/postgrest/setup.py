"""PostgREST authentication infrastructure setup.

This module sets up the core PostgREST authentication infrastructure:
- PostgreSQL extensions (pgcrypto)
- Auth schema and users table
- JWT signing/verification functions
- Database roles (anon, authenticated, analyst, admin)
- Row-Level Security policies

Usage:
    From CLI:
        $ phlo api setup-postgrest

    From Python:
        >>> from phlo.api.postgrest import setup_postgrest
        >>> setup_postgrest()
"""

import os
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def get_db_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
):
    """Get a PostgreSQL database connection.

    Args:
        host: Database host (default: from POSTGRES_HOST env var or 'localhost')
        port: Database port (default: from POSTGRES_PORT env var or 5432)
        database: Database name (default: from POSTGRES_DB env var or 'lakehouse')
        user: Database user (default: from POSTGRES_USER env var or 'lake')
        password: Database password (default: from POSTGRES_PASSWORD env var)

    Returns:
        psycopg2 connection object
    """
    conn_params = {
        "host": host or os.getenv("POSTGRES_HOST", "localhost"),
        "port": port or int(os.getenv("POSTGRES_PORT", "5432")),
        "database": database or os.getenv("POSTGRES_DB", "lakehouse"),
        "user": user or os.getenv("POSTGRES_USER", "lake"),
        "password": password or os.getenv("POSTGRES_PASSWORD", "lakepass"),
    }

    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def execute_sql_file(conn, filepath: Path, verbose: bool = True):
    """Execute a SQL file.

    Args:
        conn: Database connection
        filepath: Path to SQL file
        verbose: Print progress messages
    """
    if verbose:
        print(f"Executing: {filepath.name}")

    with open(filepath, "r") as f:
        sql_content = f.read()

    cursor = conn.cursor()
    try:
        cursor.execute(sql_content)
        if verbose:
            print(f"✓ {filepath.name} completed successfully")
    except Exception as e:
        print(f"✗ {filepath.name} failed: {e}")
        raise
    finally:
        cursor.close()


def check_if_setup_complete(conn) -> bool:
    """Check if PostgREST setup has already been completed.

    Returns:
        True if setup is complete, False otherwise
    """
    cursor = conn.cursor()
    try:
        # Check if auth schema exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.schemata
                WHERE schema_name = 'auth'
            );
        """)
        auth_exists = cursor.fetchone()[0]

        # Check if authenticator role exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_roles
                WHERE rolname = 'authenticator'
            );
        """)
        role_exists = cursor.fetchone()[0]

        return auth_exists and role_exists
    finally:
        cursor.close()


def setup_postgrest(
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    force: bool = False,
    verbose: bool = True,
):
    """Set up PostgREST authentication infrastructure.

    This function is idempotent - it's safe to run multiple times.
    It will skip setup if the infrastructure already exists unless force=True.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user (must have superuser privileges)
        password: Database password
        force: Force re-setup even if already completed
        verbose: Print progress messages

    Example:
        >>> from phlo.api.postgrest import setup_postgrest
        >>> setup_postgrest()
        Executing: 001_extensions.sql
        ✓ 001_extensions.sql completed successfully
        ...
        ✓ PostgREST setup completed successfully!
    """
    if verbose:
        print("=" * 50)
        print("PostgREST Authentication Infrastructure Setup")
        print("=" * 50)

    # Get database connection
    conn = get_db_connection(host, port, database, user, password)

    if verbose:
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), current_user;")
        db, usr = cursor.fetchone()
        print(f"Database: {db}")
        print(f"User: {usr}")
        cursor.close()
        print("=" * 50)
        print()

    # Check if already setup
    if not force and check_if_setup_complete(conn):
        if verbose:
            print("✓ PostgREST infrastructure already set up.")
            print("  Use force=True to re-apply setup.")
        conn.close()
        return

    # Get SQL files directory
    sql_dir = Path(__file__).parent / "sql"

    # Execute SQL files in order
    sql_files = sorted(sql_dir.glob("*.sql"))

    for sql_file in sql_files:
        execute_sql_file(conn, sql_file, verbose)
        if verbose:
            print()

    conn.close()

    if verbose:
        print("=" * 50)
        print("✓ PostgREST setup completed successfully!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("  1. Create your API views in the 'api' schema")
        print("  2. Start PostgREST: docker-compose up -d postgrest")
        print("  3. Test login: curl -X POST http://localhost:10018/rpc/login \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"username\": \"analyst\", \"password\": \"analyst123\"}'")


if __name__ == "__main__":
    setup_postgrest()
