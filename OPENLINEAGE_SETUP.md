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

### dbt Integration
dbt jobs are configured to emit OpenLineage events:
- Added `openlineage-dbt` to requirements
- OpenLineage env vars passed to dbt CLI invocations
- Metadata tracked for all dbt run/test operations

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

1. Run a dbt job in Dagster: http://localhost:3000
2. View lineage in Marquez Web: http://localhost:3002
3. Explore:
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
