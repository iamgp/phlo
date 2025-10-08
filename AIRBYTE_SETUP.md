# Airbyte Setup Instructions

Airbyte is configured as a separate component that can be run alongside this stack.

## Quick Start with Airbyte

```bash
# Download and run Airbyte locally
cd /tmp
git clone https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh
```

This will start Airbyte on:
- **Web UI**: http://localhost:8000
- **API**: http://localhost:8001

## Integration with Dagster

The Dagster asset-based pipeline is configured to:
1. Load Airbyte connections as Dagster assets
2. Sync data from sources to `/data/lake/raw/`
3. Trigger dbt transformations downstream

## Configure Airbyte Connection

To set up a data source in Airbyte that lands parquet files:

1. Open http://localhost:8000
2. Create a new Source (e.g., File, PostgreSQL, API)
3. Create a Destination pointing to your local filesystem or MinIO
4. Set the output path to `/data/lake/raw/bioreactor/`
5. Enable the connection

Dagster will automatically discover and materialize these as assets.

## Alternative: Run Without Airbyte

You can still run the pipeline without Airbyte by manually placing parquet files in:
```
/data/lake/raw/bioreactor/*.parquet
```

The dbt models will read from this location.
