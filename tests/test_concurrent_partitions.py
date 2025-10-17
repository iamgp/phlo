#!/usr/bin/env python3
"""
Test concurrent DLT partition writes to DuckLake.

This test validates that multiple partitions can be written concurrently without hanging,
following the same pattern as the working POC concurrency test.

Expected behavior:
- 3 concurrent partition writes complete successfully
- No hangs or timeouts
- All data written to DuckLake catalog
- Zero or minimal DuckLake retries needed
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dlt
from cascade.config import config
from cascade.dlt.ducklake_destination import build_destination as ducklake_destination


def materialize_partition(partition_date: str, worker_id: int) -> dict:
    """
    Materialize a single partition (mimics Dagster asset execution).

    This simulates the DLT asset execution for a single partition with minimal
    test data to validate concurrent write capability.
    """
    print(f"[Worker {worker_id}] Starting partition {partition_date}")
    start_time = time.time()

    pipeline_name = f"nightscout_test_{partition_date.replace('-', '_')}"
    pipelines_dir = Path.home() / ".dlt" / "pipelines" / "concurrent_test"
    pipelines_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create minimal test data for this partition
        test_data = [
            {
                "_id": f"test_{partition_date}_{i}",
                "sgv": 120 + i,
                "date": int(datetime.fromisoformat(f"{partition_date}T12:00:00").timestamp() * 1000),
                "dateString": f"{partition_date}T12:00:00.000Z",
                "direction": "Flat",
                "device": f"TestDevice{worker_id}",
                "type": "sgv"
            }
            for i in range(10)  # Just 10 rows per partition for testing
        ]

        # Create DLT pipeline
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination=ducklake_destination(),
            dataset_name=config.ducklake_default_dataset,
            pipelines_dir=str(pipelines_dir),
        )

        # Define resource
        @dlt.resource(name="entries", write_disposition="append")
        def provide_entries():
            yield test_data

        # Run pipeline
        info = pipeline.run(provide_entries())

        # Close connection properly (without ROLLBACK - let DLT manage transactions)
        try:
            if hasattr(pipeline, "_destination_client") and pipeline._destination_client:
                client = pipeline._destination_client
                if hasattr(client, "sql_client") and client.sql_client:
                    if hasattr(client.sql_client, "_conn") and client.sql_client._conn:
                        client.sql_client._conn.close()
                if hasattr(client, "close"):
                    client.close()
        except Exception:
            pass

        elapsed = time.time() - start_time
        print(f"[Worker {worker_id}] Completed partition {partition_date} in {elapsed:.2f}s")

        return {
            "worker_id": worker_id,
            "partition_date": partition_date,
            "success": True,
            "elapsed_seconds": elapsed,
            "rows_written": len(test_data),
            "error": None
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Worker {worker_id}] FAILED partition {partition_date} after {elapsed:.2f}s: {e}")

        return {
            "worker_id": worker_id,
            "partition_date": partition_date,
            "success": False,
            "elapsed_seconds": elapsed,
            "rows_written": 0,
            "error": str(e)
        }


def main():
    """Run concurrent partition test."""
    test_partitions = [
        "2024-10-13",
        "2024-10-14",
        "2024-10-15"
    ]

    print("=" * 60)
    print("CONCURRENT PARTITION WRITE TEST")
    print("=" * 60)
    print(f"Testing {len(test_partitions)} concurrent partitions:")
    for p in test_partitions:
        print(f"  - {p}")
    print()

    test_start = time.time()
    results = []

    # Use ThreadPoolExecutor like the POC (threads, not processes)
    with ThreadPoolExecutor(max_workers=len(test_partitions)) as executor:
        futures = []

        # Submit all partitions concurrently
        for i, partition in enumerate(test_partitions):
            future = executor.submit(materialize_partition, partition, i)
            futures.append(future)

        # Wait for completion with timeout
        timeout_seconds = 180  # 3 minutes
        completed_count = 0

        for future in as_completed(futures, timeout=timeout_seconds):
            try:
                result = future.result()
                results.append(result)
                completed_count += 1

                if result["success"]:
                    print(f"✓ Worker {result['worker_id']} succeeded")
                else:
                    print(f"✗ Worker {result['worker_id']} failed: {result['error']}")

            except Exception as e:
                print(f"✗ Worker future failed: {e}")
                results.append({
                    "success": False,
                    "error": str(e)
                })

    test_elapsed = time.time() - test_start

    # Report results
    print()
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"Total partitions: {len(test_partitions)}")
    print(f"Completed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {test_elapsed:.2f}s")

    if successful == len(test_partitions):
        print()
        print("✓ SUCCESS: All concurrent partitions completed")
        print()
        print("Comparison with POC results:")
        print("  POC: 4 writers, 5 minutes, 484 writes, 0 retries, 0 errors")
        print(f"  This test: {len(test_partitions)} writers, {test_elapsed:.1f}s, {successful} writes, ? retries")
        return 0
    else:
        print()
        print("✗ FAILURE: Some partitions failed or timed out")
        print()
        print("Failed partitions:")
        for r in results:
            if not r["success"]:
                print(f"  {r.get('partition_date', 'unknown')}: {r['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
