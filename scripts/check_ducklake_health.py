#!/usr/bin/env python3
"""
DuckLake Health Check Script

Verifies that DuckLake is properly configured and data flows correctly
through all layers (raw -> bronze -> silver -> gold).

Usage:
    python scripts/check_ducklake_health.py

Or from Docker:
    docker exec -it dagster-web python /opt/dagster/cascade/../scripts/check_ducklake_health.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def check_catalog_health():
    """Main health check function."""
    print("\nDuckLake Health Check")
    print("=" * 60)

    # Create connection
    print("\n[1/7] Creating DuckDB connection...")
    conn = duckdb.connect(":memory:")
    runtime = build_ducklake_runtime_config()

    print(f"  Catalog Alias: {runtime.catalog_alias}")
    print(f"  Catalog DB: {runtime.catalog_database}")
    print(f"  Data Path: {runtime.data_path}")
    print(f"  Default Dataset: {runtime.default_dataset}")

    # Configure connection
    print("\n[2/7] Configuring DuckLake connection...")
    try:
        configure_ducklake_connection(conn, runtime, read_only=True)
        print("  ✓ Connection configured successfully")
    except Exception as e:
        print(f"  ✗ Configuration failed: {e}")
        return False

    # Check extensions
    print_section("3/7 Checking Extensions")
    try:
        extensions = conn.execute(
            "SELECT extension_name, loaded FROM duckdb_extensions() "
            "WHERE extension_name IN ('ducklake', 'httpfs', 'postgres')"
        ).fetchall()

        for name, loaded in extensions:
            status = "✓" if loaded else "✗"
            print(f"  {status} {name}: {'Loaded' if loaded else 'Not loaded'}")

        if not all(loaded for _, loaded in extensions):
            print("  ✗ Some extensions not loaded")
            return False
    except Exception as e:
        print(f"  ✗ Error checking extensions: {e}")
        return False

    # Check catalog attachment
    print_section("4/7 Checking Catalog Attachment")
    try:
        databases = conn.execute("PRAGMA database_list").fetchall()
        db_map = {row[1]: row[2] for row in databases}

        if runtime.catalog_alias in db_map:
            print(f"  ✓ Catalog '{runtime.catalog_alias}' is attached")
            print(f"    Database: {db_map[runtime.catalog_alias]}")
        else:
            print(f"  ✗ Catalog '{runtime.catalog_alias}' NOT attached")
            print(f"    Available: {list(db_map.keys())}")
            return False
    except Exception as e:
        print(f"  ✗ Error checking catalog: {e}")
        return False

    # Check schemas
    print_section("5/7 Checking Schemas")
    try:
        conn.execute(f"USE {runtime.catalog_alias}")
        schemas = conn.execute(
            "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
        ).fetchall()
        schema_names = {row[0] for row in schemas}

        required_schemas = {"raw", "bronze", "silver", "gold"}
        for schema in sorted(required_schemas):
            if schema in schema_names:
                print(f"  ✓ Schema '{schema}' exists")
            else:
                print(f"  ✗ Schema '{schema}' MISSING")

        missing = required_schemas - schema_names
        if missing:
            print(f"\n  Warning: Missing schemas: {missing}")

    except Exception as e:
        print(f"  ✗ Error checking schemas: {e}")
        return False

    # Check tables in each schema
    print_section("6/7 Checking Tables by Schema")
    for schema in ["raw", "bronze", "silver", "gold"]:
        try:
            tables = conn.execute(
                f"SELECT table_name, table_type FROM {runtime.catalog_alias}.information_schema.tables "
                f"WHERE table_schema = '{schema}' ORDER BY table_name"
            ).fetchall()

            if tables:
                print(f"\n  Schema: {schema}")
                for table_name, table_type in tables:
                    print(f"    - {table_name} ({table_type})")
            else:
                print(f"\n  Schema: {schema}")
                print(f"    (no tables)")

        except Exception as e:
            print(f"\n  Schema: {schema}")
            print(f"    Error: {e}")

    # Check data counts
    print_section("7/7 Checking Row Counts")
    tables_to_check = [
        ("raw", "entries"),
        ("bronze", "stg_entries"),
        ("silver", "fct_glucose_readings"),
        ("gold", "mrt_glucose_readings"),
    ]

    for schema, table in tables_to_check:
        try:
            count = conn.execute(
                f"SELECT count(*) FROM {runtime.catalog_alias}.{schema}.{table}"
            ).fetchone()[0]
            print(f"  ✓ {schema}.{table}: {count:,} rows")
        except Exception as e:
            print(f"  ✗ {schema}.{table}: Error - {e}")

    # Summary
    print_section("Summary")
    print("  Health check completed")
    print("  Check for any ✗ marks above to identify issues")

    conn.close()
    return True


def check_postgres_catalog():
    """Check Postgres catalog health."""
    print_section("Postgres Catalog Health")
    try:
        import psycopg2

        from cascade.config import config

        conn_str = config.get_postgres_connection_string(include_db=False)
        conn = psycopg2.connect(conn_str + "/ducklake_catalog")

        cursor = conn.cursor()

        # Check for DuckLake metadata tables
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
                AND table_name LIKE 'ducklake_%'
            ORDER BY table_name
            """
        )

        tables = cursor.fetchall()
        if tables:
            print(f"\n  ✓ Found {len(tables)} DuckLake metadata tables")
            for (table_name,) in tables[:5]:
                print(f"    - {table_name}")
            if len(tables) > 5:
                print(f"    ... and {len(tables) - 5} more")
        else:
            print("  ✗ No DuckLake metadata tables found")
            print("    This might indicate the catalog hasn't been initialized")

        # Check for long-running queries/locks
        cursor.execute(
            """
            SELECT
                pid,
                state,
                wait_event_type,
                wait_event,
                EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds
            FROM pg_stat_activity
            WHERE datname = 'ducklake_catalog'
                AND state != 'idle'
            ORDER BY duration_seconds DESC
            """
        )

        active = cursor.fetchall()
        if active:
            print(f"\n  Active queries: {len(active)}")
            for pid, state, wait_type, wait_event, duration in active:
                print(
                    f"    PID {pid}: {state} ({wait_type}/{wait_event}) - {duration:.1f}s"
                )
        else:
            print("\n  ✓ No active queries (idle)")

        cursor.close()
        conn.close()

    except ImportError:
        print("  ⚠ psycopg2 not installed, skipping Postgres check")
    except Exception as e:
        print(f"  ✗ Error checking Postgres: {e}")


if __name__ == "__main__":
    success = check_catalog_health()
    check_postgres_catalog()

    sys.exit(0 if success else 1)
