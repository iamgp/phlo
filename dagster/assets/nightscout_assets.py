"""
Nightscout CGM Data Assets

This module defines assets for ingesting continuous glucose monitoring (CGM) data
from a Nightscout instance. Nightscout is an open-source CGM data platform used
by people with diabetes to monitor blood glucose levels.

Asset Flow:
    1. raw_nightscout_entries: Fetches glucose readings from Nightscout API
    2. processed_nightscout_entries: Converts to Parquet and stores in data lake
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import requests
from dagster import AssetExecutionContext, asset


@asset(
    group_name="nightscout",
    compute_kind="python",
    description="Raw glucose entries from Nightscout API",
)
def raw_nightscout_entries(context: AssetExecutionContext) -> dict[str, Any]:
    """
    Fetch glucose entries from Nightscout API.

    This asset pulls continuous glucose monitoring (CGM) data from the Nightscout
    API. Each entry represents a blood glucose reading taken every 5 minutes.

    Returns:
        Dictionary containing:
        - entries: List of glucose readings
        - count: Number of entries fetched
        - latest_timestamp: Most recent reading timestamp
    """
    base_url = "https://gwp-diabetes.fly.dev"
    endpoint = f"{base_url}/api/v1/entries.json"

    # Fetch last 7 days of data (2016 readings at 5-min intervals)
    params = {"count": 2016}

    context.log.info(f"Fetching glucose data from {endpoint}")
    response = requests.get(endpoint, params=params, timeout=30)
    response.raise_for_status()

    entries = response.json()

    context.log.info(f"Fetched {len(entries)} glucose entries")

    # Extract metadata
    if entries:
        latest = max(entries, key=lambda x: x.get("mills", 0))
        context.log.info(f"Latest reading: {latest.get('sgv')} mg/dL at {latest.get('dateString')}")

    return {
        "entries": entries,
        "count": len(entries),
        "latest_timestamp": entries[0].get("dateString") if entries else None,
    }


@asset(
    group_name="nightscout",
    compute_kind="duckdb",
    description="Processed glucose data stored as Parquet in the data lake",
    deps=[raw_nightscout_entries],
)
def processed_nightscout_entries(
    context: AssetExecutionContext, raw_nightscout_entries: dict[str, Any]
) -> str:
    """
    Convert raw Nightscout data to Parquet and store in data lake.

    This asset:
    1. Takes raw JSON entries from the API
    2. Flattens and types the data
    3. Writes to Parquet format in /data/lake/raw/nightscout/

    Parquet provides:
    - Efficient columnar storage
    - Strong typing
    - Compression (typically 10x smaller than JSON)
    - Fast analytical queries

    Returns:
        Path to the written Parquet file
    """
    entries = raw_nightscout_entries["entries"]

    if not entries:
        context.log.warning("No entries to process")
        return ""

    # Create output directory
    output_dir = Path("/data/lake/raw/nightscout")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"glucose_entries_{timestamp}.parquet"

    context.log.info(f"Processing {len(entries)} entries to {output_path}")

    # Use DuckDB to convert JSON to typed Parquet
    # This is more efficient than pandas for this use case
    con = duckdb.connect(":memory:")

    # Create temp table from JSON
    con.execute("CREATE TABLE temp_entries AS SELECT * FROM read_json_auto(?)", [json.dumps(entries)])

    # Type and clean the data, then write to Parquet
    query = """
    COPY (
        SELECT
            _id as entry_id,
            sgv as glucose_mg_dl,
            epoch_ms(mills) as timestamp,
            dateString as timestamp_iso,
            direction,
            trend,
            device,
            type,
            utcOffset as utc_offset_minutes
        FROM temp_entries
        WHERE sgv IS NOT NULL  -- Filter out null readings
        ORDER BY mills DESC
    ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
    """

    con.execute(query, [str(output_path)])
    con.close()

    context.log.info(f"Wrote Parquet file: {output_path}")
    context.log.info(f"File size: {output_path.stat().st_size / 1024:.2f} KB")

    return str(output_path)
