# Phlo Glucose Platform Demo

A demo project showing how to build a glucose monitoring data lakehouse with Phlo.
Ingests CGM (Continuous Glucose Monitor) data from Nightscout API into an Iceberg lakehouse.

## Quick Start

### Standard Mode (installs phlo from GitHub)

```bash
cd examples/glucose-platform
phlo services init
phlo services start
```

### Development Mode (uses local phlo source)

For developing phlo itself with instant iteration:

```bash
cd examples/glucose-platform
phlo services init
phlo services start --dev
```

This mounts the local `src/phlo` into the containers, so changes to phlo code
are reflected after restarting Dagster:

```bash
docker restart dagster-webserver dagster-daemon
```

## Services

After starting, access:

- **Dagster UI**: http://localhost:3000 - Orchestration & monitoring
- **Trino**: http://localhost:8080 - Query engine
- **MinIO Console**: http://localhost:9001 - Object storage (minio/minio123)
- **Superset**: http://localhost:8088 - BI dashboards (admin/admin)
- **pgweb**: http://localhost:8081 - Database admin

## Project Structure

```
glucose-platform/
├── workflows/              # Data workflows
│   ├── ingestion/         # Ingestion assets (@phlo_ingestion)
│   │   └── nightscout/    # Nightscout CGM data
│   ├── schemas/           # Pandera validation schemas
│   └── quality/           # Data quality checks
├── transforms/dbt/        # dbt transformation models
│   ├── bronze/           # Staging models (stg_*)
│   ├── silver/           # Fact tables (fct_*)
│   ├── gold/             # Aggregations & marts
│   └── marts_postgres/   # BI-ready tables
├── tests/                 # Workflow tests
└── .phlo/                 # Infrastructure config (generated)
```

## Materializing Assets

```bash
# Via CLI
phlo materialize glucose_entries --partition 2024-01-15

# Or via Dagster UI
# Navigate to Assets > glucose_entries > Materialize
```

## Data Flow

1. **Ingestion**: `glucose_entries` fetches CGM readings from Nightscout API
2. **Bronze**: `stg_glucose_entries` stages raw data
3. **Silver**: `fct_glucose_readings` adds time dimensions & categorization
4. **Gold**: `fct_daily_glucose_metrics` computes daily aggregates & time-in-range
5. **Marts**: `mrt_glucose_*` tables ready for BI dashboards

## Commands

- `phlo services start` - Start all infrastructure
- `phlo services start --dev` - Start with local phlo source mounted
- `phlo services stop` - Stop infrastructure
- `phlo services status` - Check service health
- `phlo materialize <asset>` - Materialize an asset
- `phlo test` - Run tests
