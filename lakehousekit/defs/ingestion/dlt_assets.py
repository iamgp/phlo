from __future__ import annotations

from typing import Any

import dagster as dg
import dlt
import requests

from lakehousekit.config import config
from lakehousekit.defs.partitions import daily_partition


@dg.asset(
    name="nightscout_entries",
    group_name="raw_ingestion",
    partitions_def=daily_partition,
    description="Nightscout CGM entries ingested via dlt with daily partitioning",
    compute_kind="dlt",
)
def nightscout_entries(context) -> dg.MaterializeResult:
    """
    Ingest Nightscout data for specific partition using dlt with parameterized date filtering.

    Each partition fetches data for a specific day using the Nightscout API's date range filters.
    Data is loaded into DuckDB raw schema.
    """
    partition_date = context.partition_key

    # Define start and end times for this partition (full day in UTC)
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    context.log.info(f"Fetching Nightscout entries for partition {partition_date}")

    # Create dlt pipeline targeting DuckDB
    # Use partition-specific pipeline name to avoid lock conflicts in multiprocess execution
    pipeline = dlt.pipeline(
        pipeline_name=f"nightscout_{partition_date.replace('-', '_')}",
        destination=dlt.destinations.duckdb(str(config.duckdb_path)),
        dataset_name="raw",
    )

    @dlt.resource(name="nightscout_entries", write_disposition="append")
    def get_entries() -> Any:
        """Fetch entries from Nightscout API with date range parameters."""
        response = requests.get(
            "https://gwp-diabetes.fly.dev/api/v1/entries.json",
            params={
                "count": "10000",
                "find[dateString][$gte]": start_time,
                "find[dateString][$lt]": end_time,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        context.log.info(f"Fetched {len(data)} entries from Nightscout API")
        yield data

    # Run the pipeline
    info = pipeline.run(get_entries())

    # Extract metrics
    rows_loaded = info.metrics.get("data", {}).get("rows", 0)

    return dg.MaterializeResult(
        metadata={
            "partition_date": dg.MetadataValue.text(partition_date),
            "rows_loaded": dg.MetadataValue.int(rows_loaded),
            "start_time": dg.MetadataValue.text(start_time),
            "end_time": dg.MetadataValue.text(end_time),
        }
    )
