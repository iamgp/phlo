# analyst_duckdb_demo.py - Example script demonstrating analyst workflow with DuckDB
# Shows how data analysts can query Iceberg tables directly from laptops
# using DuckDB, bypassing the need for Docker access to the full platform

#!/usr/bin/env python3
"""
Analyst DuckDB Demo - Query Iceberg tables from your laptop

This demonstrates the analyst workflow for querying Phlo's Iceberg tables
directly using DuckDB, without needing access to Docker or the pipeline.

Prerequisites:
1. Install DuckDB: pip install duckdb
2. Ensure MinIO is accessible (default: localhost:10001)
3. Know your MinIO credentials from .env file

Usage:
    python examples/analyst_duckdb_demo.py
"""

import os
import sys


# --- Main Demonstration Function ---
# Walks through the complete analyst workflow step by step
def main():
    """Demonstrate querying Iceberg tables with DuckDB from your laptop."""

    print("=" * 60)
    print("Phlo Analyst Workflow: DuckDB + Iceberg")
    print("=" * 60)
    print()

    # Step 1: Check DuckDB installation
    print("Step 1: Checking DuckDB installation...")
    try:
        import duckdb

        print(f"✓ DuckDB {duckdb.__version__} installed")
    except ImportError:
        print("✗ DuckDB not installed")
        print()
        print("Install DuckDB:")
        print("  pip install duckdb")
        print()
        return 1

    print()

    # Step 2: Create connection
    print("Step 2: Creating DuckDB connection...")
    conn = duckdb.connect(":memory:")
    print("✓ Connected to DuckDB")
    print()

    # Step 3: Install Iceberg extension
    print("Step 3: Installing Iceberg extension...")
    try:
        conn.execute("INSTALL iceberg")
        conn.execute("LOAD iceberg")
        print("✓ Iceberg extension loaded")
    except Exception as e:
        print(f"✗ Failed to load Iceberg extension: {e}")
        return 1

    print()

    # Step 4: Configure MinIO connection
    print("Step 4: Configuring MinIO connection...")
    print("  Reading credentials from environment...")

    minio_host = os.getenv("MINIO_HOST", "localhost")
    minio_port = os.getenv("MINIO_API_PORT", "10001")
    minio_user = os.getenv("MINIO_ROOT_USER", "minio")
    minio_password = os.getenv("MINIO_ROOT_PASSWORD", "minio123")

    endpoint = f"{minio_host}:{minio_port}"

    try:
        conn.execute(f"SET s3_endpoint = '{endpoint}'")
        conn.execute("SET s3_use_ssl = false")
        conn.execute("SET s3_url_style = 'path'")
        conn.execute(f"SET s3_access_key_id = '{minio_user}'")
        conn.execute(f"SET s3_secret_access_key = '{minio_password}'")
        print(f"✓ Connected to MinIO at {endpoint}")
        print(f"  Using credentials: {minio_user}/*****")
    except Exception as e:
        print(f"✗ Failed to configure MinIO: {e}")
        return 1

    print()

    # Step 5: Get Iceberg table location
    print("Step 5: Finding Iceberg table metadata location...")
    print("  (Analysts get this from their data engineering team)")
    print()

    # In a real analyst workflow, the data team provides the metadata location
    # Here's how they get it (run this inside the container):
    print("  To get the metadata location, run inside Docker:")
    print("  -------------------------------------------------------")
    print('  docker compose exec dagster-webserver python -c "')
    print("  from phlo_iceberg.catalog import get_catalog")
    print("  table = get_catalog(ref='main').load_table('raw.entries')")
    print("  print(table.metadata_location)")
    print('  "')
    print("  -------------------------------------------------------")
    print()

    # For this demo, let's try to discover it automatically via MinIO listing
    print("  Attempting to auto-discover metadata location...")

    # Try to find metadata files in MinIO
    metadata_location = None

    try:
        # List metadata files in the expected location
        import subprocess

        result = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "dagster-webserver",
                "python",
                "-c",
                "from phlo_iceberg.catalog import get_catalog; "
                "table = get_catalog(ref='main').load_table('raw.entries'); "
                "print(table.metadata_location)",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            metadata_location = result.stdout.strip()
            print("✓ Auto-discovered metadata location:")
            print(f"  {metadata_location}")
        else:
            raise Exception("Failed to auto-discover")

    except Exception:
        print("  ⚠ Auto-discovery failed (Docker not accessible)")
        print()
        print("  Analysts: Get the metadata location from your data team")
        print("  Example format:")
        print("    s3://lake/warehouse/raw/entries_<UUID>/metadata/<version>.metadata.json")
        print()
        print("  For now, skipping table query demo...")
        print()
        print("  Once you have the metadata location, you can query like this:")
        print("""
  import duckdb
  conn = duckdb.connect()
  conn.execute("INSTALL iceberg; LOAD iceberg")
  conn.execute("SET s3_endpoint = 'localhost:10001'")
  conn.execute("SET s3_use_ssl = false")
  conn.execute("SET s3_url_style = 'path'")
  conn.execute("SET s3_access_key_id = 'minio'")
  conn.execute("SET s3_secret_access_key = 'minio123'")

  # Replace with actual metadata location from your data team
  metadata = 's3://lake/warehouse/raw/entries_<UUID>/metadata/<version>.metadata.json'

  df = conn.execute(f"SELECT * FROM iceberg_scan('{metadata}') LIMIT 10").df()
  print(df)
        """)
        return 0

    if not metadata_location:
        print("  ⚠ Could not find table metadata")
        return 0

    print()

    # Step 6: Query the table!
    print("Step 6: Querying Iceberg table with DuckDB...")
    print()

    try:
        # Count total rows
        result = conn.execute(f"""
        SELECT COUNT(*) as total_rows
        FROM iceberg_scan('{metadata_location}')
        """).fetchone()

        if result:
            total_rows = result[0]
        else:
            total_rows = 0
        print(f"✓ Total rows in raw.entries: {total_rows:,}")

        if total_rows == 0:
            print()
            print("⚠ Table is empty. Run ingestion to load data.")
            return 0

        # Get date range
        result = conn.execute(f"""
        SELECT
        MIN(date) as min_date,
        MAX(date) as max_date,
        COUNT(DISTINCT date_string::DATE) as distinct_days
        FROM iceberg_scan('{metadata_location}')
        """).fetchone()

        if result:
            print(f"✓ Date range: {result[0]} to {result[1]}")
            print(f"✓ Distinct days: {result[2]}")
        else:
            print("✓ No date range available")

        # Sample data
        print()
        print("Sample glucose readings:")
        print("-" * 60)

        result = conn.execute(f"""
            SELECT
                date_string,
                sgv,
                direction,
                device
            FROM iceberg_scan('{metadata_location}')
            ORDER BY date DESC
            LIMIT 10
        """).fetchall()

        print(f"{'Date':<25} {'SGV':>5} {'Dir':<10} {'Device':<20}")
        print("-" * 60)
        for row in result:
            date_str = row[0] if row[0] else "N/A"
            sgv = row[1] if row[1] else 0
            direction = row[2] if row[2] else "N/A"
            device = row[3] if row[3] else "N/A"
            print(f"{date_str:<25} {sgv:>5} {direction:<10} {device:<20}")

        print()

        # Daily statistics
        print("Daily statistics (last 7 days):")
        print("-" * 60)

        # Get the last 7 days of data (DuckDB interval syntax)
        result = conn.execute(f"""
            WITH max_date AS (
                SELECT MAX(date) as max_dt
                FROM iceberg_scan('{metadata_location}')
            )
            SELECT
                date_string::DATE as day,
                COUNT(*) as readings,
                ROUND(AVG(sgv), 1) as avg_glucose,
                MIN(sgv) as min_glucose,
                MAX(sgv) as max_glucose
            FROM iceberg_scan('{metadata_location}')
            CROSS JOIN max_date
            WHERE date >= max_dt - (7 * 24 * 60 * 60 * 1000)  -- 7 days in milliseconds
            AND sgv IS NOT NULL
            GROUP BY date_string::DATE
            ORDER BY day DESC
            LIMIT 7
        """).fetchall()

        print(f"{'Date':<12} {'Readings':>10} {'Avg':>8} {'Min':>6} {'Max':>6}")
        print("-" * 60)
        for row in result:
            print(f"{str(row[0]):<12} {row[1]:>10} {row[2]:>8} {row[3]:>6} {row[4]:>6}")

        print()

    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Success!
    print()
    print("=" * 60)
    print("Success! You can now query Iceberg tables with DuckDB")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Try your own queries (see docs/duckdb-iceberg-queries.md)")
    print("  2. Export to CSV for further analysis")
    print("  3. Use in Jupyter notebooks for visualization")
    print()
    print("Example query to copy:")
    print(f"""
import duckdb
conn = duckdb.connect()
conn.execute("INSTALL iceberg; LOAD iceberg")
conn.execute("SET s3_endpoint = '{endpoint}'")
conn.execute("SET s3_use_ssl = false")
conn.execute("SET s3_url_style = 'path'")
conn.execute("SET s3_access_key_id = '{minio_user}'")
conn.execute("SET s3_secret_access_key = '***'")

df = conn.execute('''
    SELECT * FROM iceberg_scan('{metadata_location}')
    WHERE date >= CURRENT_TIMESTAMP - INTERVAL 1 DAY
''').df()

print(df.head())
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
