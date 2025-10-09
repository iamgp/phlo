import subprocess

from dagster import AssetExecutionContext, AssetIn, AssetKey, asset


@asset(
    group_name="metadata",
    description="Ingest dbt artifacts into DataHub for lineage and dataset metadata.",
    ins={"publish_glucose_marts_to_postgres": AssetIn(key=AssetKey("publish_glucose_marts_to_postgres"))},
)
def ingest_dbt_to_datahub(context: AssetExecutionContext, publish_glucose_marts_to_postgres):
    del publish_glucose_marts_to_postgres

    command = ["datahub", "ingest", "-c", "/opt/dagster/ingestion/datahub_dbt.yml"]
    context.log.info("Running DataHub ingestion CLI to publish dbt metadata.")
    proc = subprocess.run(command, capture_output=True, text=True)

    context.log.info(proc.stdout)
    if proc.stderr:
        context.log.warning(proc.stderr)

    if proc.returncode != 0:
        raise RuntimeError(
            f"DataHub ingestion failed with exit code {proc.returncode}. "
            "See logs for details."
        )

    return "dbt metadata ingested"
