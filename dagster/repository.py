import os

from dagster import AssetSelection, Definitions, ScheduleDefinition, define_asset_job
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCliResource

from assets.datahub_assets import ingest_dbt_to_datahub
from assets.dbt_assets import DBT_PROFILES_DIR, DBT_PROJECT_DIR, all_dbt_assets
from assets.publish_assets import publish_glucose_marts_to_postgres
from assets.raw_data_assets import raw_bioreactor_data
from assets.nightscout_validations import nightscout_glucose_quality_check

# Airbyte configuration
airbyte_host = os.getenv("AIRBYTE_HOST", "airbyte-server")
airbyte_port = os.getenv("AIRBYTE_API_PORT", "8001")

airbyte_resource = AirbyteResource(
    host=airbyte_host,
    port=airbyte_port,
)

# Build Airbyte assets from configured connections
try:
    from dagster_airbyte import build_airbyte_assets

    airbyte_assets = build_airbyte_assets(
        connection_id="015ab542-1a18-4156-a44a-861b17f8d03c",
        destination_tables=["nightscout_entries"],
        group_name="raw_ingestion",
    )
except Exception as e:
    print(f"Could not load Airbyte assets: {e}")
    airbyte_assets = None

# Define asset jobs
ingest_job = define_asset_job(
    name="ingest_raw_data",
    selection=AssetSelection.groups("raw_ingestion"),
    description="Sync data from sources via Airbyte",
)

transform_job = define_asset_job(
    name="transform_dbt_models",
    selection=AssetSelection.all(),
    description="Run all dbt models: staging → intermediate → curated → marts",
)

# Nightly schedule for the full pipeline
nightly_pipeline_schedule = ScheduleDefinition(
    name="nightly_pipeline",
    job=transform_job,
    cron_schedule="0 2 * * *",  # 02:00 nightly
    execution_timezone="Europe/London",
)

# Main definitions
all_assets = [
    raw_bioreactor_data,
    all_dbt_assets,
    publish_glucose_marts_to_postgres,
    ingest_dbt_to_datahub,
]
if airbyte_assets is not None:
    all_assets.extend(airbyte_assets)

defs = Definitions(
    assets=all_assets,
    asset_checks=[nightscout_glucose_quality_check],
    jobs=[
        ingest_job,
        transform_job,
    ],
    schedules=[nightly_pipeline_schedule],
    resources={
        "dbt": DbtCliResource(
            project_dir=str(DBT_PROJECT_DIR),
            profiles_dir=str(DBT_PROFILES_DIR),
        ),
        "airbyte": airbyte_resource,
    },
)
