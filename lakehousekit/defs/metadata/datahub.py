from __future__ import annotations

import subprocess

from dagster import AssetExecutionContext, AssetIn, AssetKey, asset

from lakehousekit.schemas import DatahubIngestionOutput, PublishPostgresOutput


@asset(
    group_name="metadata",
    description="Ingest dbt artifacts into DataHub for lineage and dataset metadata.",
    ins={
        "publish_glucose_marts_to_postgres": AssetIn(
            key=AssetKey("publish_glucose_marts_to_postgres")
        )
    },
)
def ingest_dbt_to_datahub(
    context: AssetExecutionContext,
    publish_glucose_marts_to_postgres: PublishPostgresOutput,
) -> DatahubIngestionOutput:
    context.log.info(
        "Received publishing stats for %d tables",
        len(publish_glucose_marts_to_postgres.tables),
    )

    command = ["datahub", "ingest", "-c", "/opt/dagster/ingestion/datahub_dbt.yml"]
    context.log.info("Running DataHub ingestion CLI to publish dbt metadata")
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        context.log.error("DataHub ingestion timed out after 300 seconds")
        raise

    context.log.info(proc.stdout)
    if proc.stderr:
        context.log.warning(proc.stderr)

    if proc.returncode != 0:
        context.log.error(
            "DataHub ingestion failed with exit code %s", proc.returncode
        )
        raise RuntimeError(
            f"DataHub ingestion failed with exit code {proc.returncode}. "
            "See logs for details."
        )

    tables_processed = len(publish_glucose_marts_to_postgres.tables)
    return DatahubIngestionOutput(
        status="dbt metadata ingested successfully",
        tables_processed=tables_processed,
    )
