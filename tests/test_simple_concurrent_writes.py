#!/usr/bin/env python3
"""
Simple concurrent write test directly to DuckLake (without DLT).

This test validates that DuckLake+Postgres supports concurrent writes
by directly using DuckDB connections, bypassing DLT entirely.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dataclasses
import duckdb
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection


def concurrent_writer(worker_id: int, num_rows: int) -> dict:
    """Write data concurrently to DuckLake."""
    print(f"[Worker {worker_id}] Starting")
    start_time = time.time()

    try:
        # Create separate in-memory instance (like POC)
        conn = duckdb.connect(database="")
        runtime = build_ducklake_runtime_config()

        # Override retry settings to match POC
        runtime = dataclasses.replace(
            runtime,
            ducklake_retry_count=100,
            ducklake_retry_wait_ms=100,
            ducklake_retry_backoff=2.0,
        )

        # Configure connection
        configure_ducklake_connection(conn, runtime, ensure_schemas={"raw"})

        # Create test table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw.concurrent_test (
                id INTEGER,
                worker_id INTEGER,
                value VARCHAR,
                timestamp TIMESTAMP
            )
        """)

        # Write data in explicit transaction (like POC)
        conn.execute("BEGIN TRANSACTION")
        try:
            for i in range(num_rows):
                conn.execute("""
                    INSERT INTO raw.concurrent_test (id, worker_id, value, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, [i, worker_id, f"worker{worker_id}_row{i}"])

            conn.execute("COMMIT")
        except Exception as e:
            try:
                conn.execute("ROLLBACK")
            except:
                pass
            raise

        # Close connection
        conn.close()

        elapsed = time.time() - start_time
        print(f"[Worker {worker_id}] Completed in {elapsed:.2f}s")

        return {
            "worker_id": worker_id,
            "success": True,
            "elapsed_seconds": elapsed,
            "rows_written": num_rows,
            "error": None
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Worker {worker_id}] FAILED after {elapsed:.2f}s: {e}")

        return {
            "worker_id": worker_id,
            "success": False,
            "elapsed_seconds": elapsed,
            "rows_written": 0,
            "error": str(e)
        }


def main():
    """Run simple concurrent write test."""
    num_workers = 3
    rows_per_worker = 10

    print("=" * 60)
    print("SIMPLE CONCURRENT WRITE TEST (NO DLT)")
    print("=" * 60)
    print(f"Workers: {num_workers}")
    print(f"Rows per worker: {rows_per_worker}")
    print()

    test_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        for i in range(num_workers):
            future = executor.submit(concurrent_writer, i, rows_per_worker)
            futures.append(future)

        timeout_seconds = 60
        for future in as_completed(futures, timeout=timeout_seconds):
            try:
                result = future.result()
                results.append(result)

                if result["success"]:
                    print(f"✓ Worker {result['worker_id']} succeeded")
                else:
                    print(f"✗ Worker {result['worker_id']} failed: {result['error']}")

            except Exception as e:
                print(f"✗ Worker future failed: {e}")
                results.append({"success": False, "error": str(e)})

    test_elapsed = time.time() - test_start

    print()
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"Workers: {num_workers}")
    print(f"Completed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {test_elapsed:.2f}s")

    if successful == num_workers:
        print()
        print("✓ SUCCESS: All concurrent writes completed")
        return 0
    else:
        print()
        print("✗ FAILURE: Some writes failed or timed out")
        return 1


if __name__ == "__main__":
    sys.exit(main())
