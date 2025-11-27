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
├── contracts/              # Data contracts (SLAs, schema agreements)
│   └── glucose_readings.yaml
├── workflows/              # Data workflows
│   ├── ingestion/         # Ingestion assets (@phlo_ingestion)
│   │   └── nightscout/    # Nightscout CGM data
│   ├── schemas/           # Pandera validation schemas
│   └── quality/           # Data quality checks (@phlo.quality)
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
# Single materialization
phlo materialize glucose_entries --partition 2024-01-15

# Backfill date range
phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31

# Parallel backfill
phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-12-31 --parallel 4

# Via Dagster UI
# Navigate to Assets > glucose_entries > Materialize
```

## Data Flow

1. **Ingestion**: `glucose_entries` fetches CGM readings from Nightscout API
2. **Bronze**: `stg_glucose_entries` stages raw data
3. **Silver**: `fct_glucose_readings` adds time dimensions & categorization
4. **Gold**: `fct_daily_glucose_metrics` computes daily aggregates & time-in-range
5. **Marts**: `mrt_glucose_*` tables ready for BI dashboards

## CLI Commands

### Core Operations

```bash
phlo services start       # Start all infrastructure
phlo services stop        # Stop infrastructure
phlo services status      # Check service health
phlo materialize <asset>  # Materialize an asset
phlo backfill <asset>     # Backfill partitions
phlo test                 # Run tests
```

### Logs & Monitoring

```bash
phlo logs                        # View recent logs
phlo logs --asset glucose_entries # Filter by asset
phlo logs --level ERROR --since 1h
phlo logs --follow               # Real-time tail

phlo metrics                     # Summary dashboard
phlo metrics asset glucose_entries
```

### Lineage & Impact Analysis

```bash
phlo lineage show glucose_entries
phlo lineage show glucose_entries --downstream
phlo lineage impact glucose_entries
```

### Schema & Catalog

```bash
phlo schema list
phlo schema show RawGlucoseEntries

phlo catalog tables
phlo catalog describe raw.glucose_entries
phlo catalog history raw.glucose_entries
```

### Data Contracts

```bash
phlo contract list
phlo contract show glucose_readings
phlo contract validate glucose_readings
```

## Data Contracts

This project includes data contracts in `contracts/` that define:

- **Schema requirements**: Required columns, types, and constraints
- **SLAs**: Freshness (2 hours), quality threshold (99%)
- **Consumers**: Teams that depend on this data

Example contract (`contracts/glucose_readings.yaml`):

```yaml
name: glucose_readings
version: 1.0.0
owner: data-team

schema:
  required_columns:
    - name: sgv
      type: integer
      constraints:
        min: 20
        max: 600

sla:
  freshness_hours: 2
  quality_threshold: 0.99

consumers:
  - name: analytics-team
    usage: BI dashboards
```

Validate contracts before deployment:

```bash
phlo contract validate glucose_readings
```

## Quality Framework

Quality checks use the `@phlo.quality` decorator and Pandera schemas:

```python
from phlo.quality import NullCheck, RangeCheck
import phlo

@phlo.quality(
    table="silver.fct_glucose_readings",
    checks=[
        NullCheck(columns=["sgv", "reading_timestamp"]),
        RangeCheck(column="sgv", min_value=20, max_value=600),
    ],
    group="nightscout",
    blocking=True,
)
def glucose_quality():
    pass
```

See `workflows/quality/nightscout.py` for the full implementation using Pandera schemas
