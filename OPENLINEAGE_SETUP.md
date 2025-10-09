# OpenLineage + Marquez Integration

This branch adds OpenLineage data lineage tracking using Marquez as the lineage backend.

## Services Added

### Marquez API
- **URL**: http://localhost:5555
- **Admin Port**: http://localhost:5556
- **Purpose**: OpenLineage backend server for collecting lineage metadata

### Marquez Web UI
- **URL**: http://localhost:3002
- **Purpose**: Visual interface for exploring data lineage graphs

## Configuration

### Environment Variables (.env)
```bash
MARQUEZ_PORT=5555
MARQUEZ_ADMIN_PORT=5556
MARQUEZ_WEB_PORT=3002
```

### Database Setup
Marquez requires its own database with dedicated user:
- Database: `marquez`
- User: `marquez`
- Password: `marquez`

The database is automatically created on first startup.

### Dagster Integration
Dagster is configured to emit OpenLineage events:
- Added `openlineage-dagster` to requirements
- Environment variables set:
  - `OPENLINEAGE_URL=http://marquez:5000`
  - `OPENLINEAGE_NAMESPACE=lakehouse`
- A Dagster sensor (`openlineage_sensor`) tails the event log and forwards run/step events to Marquez. The sensor is defined in `dagster/repository.py` and is picked up by the `dagster-daemon` process (restart the Dagster containers after changes with `docker compose restart dagster-web dagster-daemon`).
- A lightweight lineage asset (`nightscout_airbyte_lineage`) emits ingestion lineage for the Nightscout Airbyte sync, linking the Nightscout API to the raw landing zone in Marquez.

### dbt Integration
dbt jobs are configured to emit OpenLineage events:
- Added `openlineage-dbt` to requirements
- The `dbt_assets` executor now parses dbt artifacts and calls `openlineage-dbt` after each run, emitting dataset and column lineage into Marquez (namespace `duckdb:///data/duckdb/warehouse.duckdb`).
- OpenLineage env vars are set before invoking dbt so that build/test operations are captured automatically.

## How It Works

1. **Dagster Jobs**: When jobs run, they emit OpenLineage events to Marquez API
2. **dbt Models**: dbt transformations send lineage metadata including:
   - Source datasets
   - Target datasets
   - Column-level lineage
   - Transformation logic
3. **Marquez**: Stores and aggregates lineage metadata
4. **Marquez Web**: Visualizes the complete data pipeline lineage

## Accessing Lineage

1. Run any Dagster job or asset materialization (e.g. trigger the `transform_dbt_models` job from Dagit at http://localhost:3000).
2. Confirm the OpenLineage sensor is running: in Dagit, open **Sensors** and ensure `openlineage_sensor` is ``On``. If it is off, toggle it on.
3. View lineage in Marquez Web: http://localhost:3002
4. Explore:
   - Datasets and their relationships
   - Job runs and history
   - Column-level lineage
   - Data quality checks

## Platform Notes

Marquez images are AMD64-only. On ARM64 (Apple Silicon), Docker automatically uses Rosetta 2 emulation. The setup includes `platform: linux/amd64` to ensure proper emulation.

## Next Steps

Once Dagster is rebuilt with OpenLineage dependencies:
1. Trigger a dbt job run
2. Check Marquez UI for lineage data
3. Explore the complete pipeline graph
