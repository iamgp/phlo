# DataHub Lineage Integration

This branch swaps Marquez for DataHub to catalog the Dagster + dbt + Airbyte pipeline. The stack now emits metadata to DataHub via the dbt artifacts and the ingestion CLI.

## Services Added

### DataHub GMS
- **URL:** http://localhost:8080
- REST endpoint used by Dagster and ingestion jobs.

### DataHub Frontend
- **URL:** http://localhost:9002
- Web UI for browsing datasets, lineage, ownership, documentation.

### Supporting services
- Kafka, Schema Registry, MySQL, Elasticsearch, MAE/MCE consumers, and Actions services are deployed via Docker Compose (see `docker-compose.yml`).

## Dagster Integration
- `dagster/assets/dbt_assets.py` runs `dbt build` followed by `dbt docs generate` to produce `manifest.json` and `catalog.json` artifacts.
- `dagster/assets/datahub_assets.py` defines the `ingest_dbt_to_datahub` asset. It runs `datahub ingest -c /opt/dagster/ingestion/datahub_dbt.yml` to push the dbt metadata into DataHub after marts are published.
- The ingestion recipe (`dagster/ingestion/datahub_dbt.yml`) points at DataHub GMS and the dbt artifacts under `/dbt/target/`.

## Running the stack
1. Rebuild the Dagster image to install the DataHub CLI:
   ```bash
   docker compose build dagster-webserver dagster-daemon
   ```
2. Start everything (DataHub replaces Marquez):
   ```bash
   docker compose up -d
   ```
3. Trigger the Dagster pipeline (`transform_dbt_models`), which will:
   - Sync data via Airbyte
   - Run dbt build + docs generate
   - Publish marts to Postgres
   - Ingest dbt metadata into DataHub

## Exploring lineage
- Open the DataHub UI at http://localhost:9002 (login: `datahub` / `datahub`).
- Browse **Datasets** or **Lineage** to see the DuckDB models, Postgres marts, and their upstream sources.
- Column-level lineage is available because the dbt catalog contains column metadata.

## Additional ingest jobs
- You can add more DataHub recipes (Airbyte, Superset, custom sources) under `dagster/ingestion/` and invoke them from additional Dagster assets if you want to enrich the catalog further.
