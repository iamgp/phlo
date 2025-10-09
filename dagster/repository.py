import os
from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    AssetSelection,
)
from dagster_dbt import DbtCliResource
from dagster_airbyte import AirbyteResource

from assets.dbt_assets import (
    dbt_nightscout_staging,
    dbt_bioreactor_staging,
    dbt_curated,
    dbt_postgres_marts,
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
)
from assets.raw_data_assets import raw_bioreactor_data
from assets.nightscout_assets import raw_nightscout_entries, processed_nightscout_entries
from resource.openlineage import OpenLineageResource

# Note: GE validation asset disabled due to pandas compatibility in Docker
# Re-enable once pandas 2.x compatibility is resolved

# Airbyte is optional - only load assets if configured
airbyte_host = os.getenv("AIRBYTE_HOST", "localhost")
airbyte_port = os.getenv("AIRBYTE_API_PORT", "8001")

airbyte_resource = AirbyteResource(
    host=airbyte_host,
    port=airbyte_port,
)

# Build Airbyte assets if Airbyte is available
# For now, we'll skip automatic loading since Airbyte isn't running
airbyte_assets = []  # build_airbyte_assets(airbyte_resource) when Airbyte is configured

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
defs = Definitions(
    assets=[
        raw_bioreactor_data,
        raw_nightscout_entries,
        processed_nightscout_entries,
        dbt_nightscout_staging,
        dbt_bioreactor_staging,
        dbt_curated,
        dbt_postgres_marts,
        *airbyte_assets,
    ],
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
        "openlineage": OpenLineageResource(
            url="http://marquez:5000",
            namespace="lakehouse",
        ),
    },
)
