from dagster import job, op

@op
def trigger_airbyte_connections():
    # Minimal placeholder: call Airbyte API if profile enabled.
    # You can wire DAGSTER env vars and requests to POST /api/v1/jobs
    pass

@job
def airbyte_ingest_job():
    trigger_airbyte_connections()
