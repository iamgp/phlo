# Phlo Platform Demonstrations

Welcome to the Phlo platform demos! These resources showcase how to build production-ready data platforms using Phlo's modern lakehouse architecture.

## 🎯 Key Concept: Phlo as an Installable Package

**Phlo is a framework you install, not a repository you fork!**

```
┌──────────────────────────────────────┐
│   PHLO PACKAGE (Framework)          │   pip install phlo
│   • Decorators, CLI, core tools     │
└──────────────────────────────────────┘
                ↓ uses
┌──────────────────────────────────────┐
│   YOUR PROJECT (Workflows)           │   phlo init my-platform
│   • Your schemas, APIs, dbt models  │
└──────────────────────────────────────┘
```

**Separation:** Your workflow code lives in YOUR project, not in the Phlo package!

---

## Available Demos

### 🌟 START HERE: Phlo as an Installable Package

**[PHLO_AS_PACKAGE_DEMO.md](./PHLO_AS_PACKAGE_DEMO.md)** - **READ THIS FIRST!**

Explains the critical separation between:
- **Phlo package** (framework you install via pip)
- **Your project** (workflows you create with `phlo init`)

This is the foundation for understanding how Phlo works!

---

### 1. Glucose Monitoring Platform

A complete, real-world example of a healthcare data platform for continuous glucose monitoring (CGM).

**Files:**
- **[QUICKSTART_GLUCOSE_PLATFORM.md](./QUICKSTART_GLUCOSE_PLATFORM.md)** - 15-minute quick start guide
- **[GLUCOSE_PLATFORM_DEMO.md](./GLUCOSE_PLATFORM_DEMO.md)** - Comprehensive deep dive (shows current example in phlo repo)
- **[glucose_platform_demo.py](../../examples/glucose_platform_demo.py)** - Interactive demo script

**Note:** The current glucose example lives in the Phlo repo for demonstration. In practice, you would create this using `phlo init` as shown in the package demo above!

**What You'll Learn:**
- Building data pipelines with `@phlo_ingestion` decorator
- Multi-layered data validation with Pandera
- dbt transformations (Bronze → Silver → Gold → Marts)
- Auto-generated REST/GraphQL APIs
- Git-like branching for data development
- Quality gates and data governance

**Use Cases:**
- Healthcare analytics
- IoT sensor data
- Time-series monitoring
- Real-time dashboards

---

## Quick Start

### Run the Interactive Demo

```bash
# Install dependencies
pip install -e ".[dev]"
pip install rich requests

# Run the full demo
python examples/glucose_platform_demo.py

# Or run specific sections
python examples/glucose_platform_demo.py --demo architecture
python examples/glucose_platform_demo.py --demo ingestion
python examples/glucose_platform_demo.py --demo analytics
python examples/glucose_platform_demo.py --demo api
```

### Build Your Own Platform (15 minutes)

Follow the [Quick Start Guide](./QUICKSTART_GLUCOSE_PLATFORM.md):

1. Start services with `docker compose up -d`
2. Run ingestion: `dagster asset materialize -m phlo --select glucose_entries`
3. Transform data: `dbt run --models +mrt_glucose_overview`
4. Access APIs: `curl http://localhost:3001/mrt_glucose_overview`

---

## Demo Comparison

| Demo | Type | Time | Best For |
|------|------|------|----------|
| **Quick Start** | Hands-on tutorial | 15 min | Getting started quickly |
| **Comprehensive Guide** | Deep dive | 45 min | Understanding architecture |
| **Interactive Script** | Automated demo | 5 min | Visual walkthrough |

---

## Demo Architecture

All demos showcase this architecture:

```
External API (Nightscout)
    ↓
[@phlo_ingestion decorator]
    ↓
DLT Pipeline → S3/MinIO Staging
    ↓
PyIceberg Merge (dev branch)
    ↓
dbt Transformations
  ├─ Bronze: Staging (clean raw data)
  ├─ Silver: Facts (business logic)
  ├─ Gold: Aggregates (KPIs)
  └─ Marts: BI-ready views
    ↓
PostgreSQL Publishing
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  PostgREST  │   Hasura    │  Superset   │   DuckDB    │
│ (REST API)  │  (GraphQL)  │ (Dashboards)│ (Analysts)  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## Technology Stack

### Storage & Catalog
- **Apache Iceberg** - ACID transactions, schema evolution, time travel
- **Project Nessie** - Git-like branching for data
- **MinIO** - S3-compatible object storage

### Ingestion & Transformation
- **DLT (Data Load Tool)** - Data ingestion framework
- **dbt** - SQL-based transformations
- **Pandera** - DataFrame validation

### Orchestration & Quality
- **Dagster** - Asset-based orchestration with lineage
- **Pandera Checks** - Multi-layered validation
- **dbt Tests** - Data quality tests

### APIs & Analytics
- **PostgREST** - Auto-generated REST API
- **Hasura** - GraphQL API with subscriptions
- **Superset** - Business intelligence dashboards
- **DuckDB** - Direct Iceberg queries for analysts

---

## Key Features Demonstrated

### 1. Declarative Pipelines

**Traditional approach:** 270+ lines per asset
```python
# Lots of boilerplate for:
# - Schema definition
# - Table creation
# - Validation logic
# - Deduplication
# - Error handling
# - Metadata tracking
```

**Phlo approach:** ~60 lines with decorator
```python
@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,
    group="nightscout",
)
def glucose_entries(partition_date: str):
    return rest_api({...})  # Just define the source
```

### 2. Schema-First Development

Define schemas once with Pandera:
```python
class RawGlucoseEntries(DataFrameModel):
    _id: str = Field(nullable=False, unique=True)
    sgv: int = Field(ge=1, le=1000)
```

Used for:
- ✅ Data validation (ingestion time)
- ✅ Iceberg table schema (auto-generated)
- ✅ Documentation (self-describing)
- ✅ Type hints (IDE support)

### 3. Git-Like Data Branching

```bash
# Develop on dev branch
dagster asset materialize --select glucose_entries  # writes to dev

# Run quality checks
dagster asset validate --select fct_glucose_readings

# Merge to production
phlo nessie merge dev main  # only if checks pass

# Time travel
SELECT * FROM glucose_entries FOR VERSION AS OF 'yesterday'
```

### 4. Quality Gates

Multi-layered validation prevents bad data from reaching production:

```
Layer 1: Ingestion ─┬─ PASS ──→ Continue
                    └─ FAIL ──→ Block (don't ingest)

Layer 2: Transform ─┬─ PASS ──→ Continue
                    └─ FAIL ──→ Warn (log issue)

Layer 3: Checks ────┬─ PASS ──→ Allow merge to main
                    └─ FAIL ──→ Block promotion

Layer 4: Publishing ┬─ PASS ──→ Publish to PostgreSQL
                    └─ FAIL ──→ Block publish
```

### 5. Auto-Generated APIs

From dbt models to production APIs in seconds:

```sql
-- transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql
select reading_date, avg_glucose_mg_dl, time_in_range_pct
from {{ ref('fct_daily_glucose_metrics') }}
```

Automatically creates:

**REST API:**
```bash
GET /mrt_glucose_overview?order=reading_date.desc
```

**GraphQL API:**
```graphql
query { mrt_glucose_overview { reading_date avg_glucose_mg_dl } }
```

---

## Real-World Use Cases

### Healthcare (Glucose Demo)
- **Data source:** Nightscout API (continuous glucose monitoring)
- **Metrics:** Time in range, estimated A1C, hypoglycemia alerts
- **Users:** Patients, doctors, researchers

### IoT Sensor Data
- **Adapt for:** Weather stations, industrial sensors, smart home
- **Pattern:** Same architecture, different source
- **Code reuse:** 90%+ via `@phlo_ingestion`

### Financial Data
- **Adapt for:** Stock prices, transaction data, market feeds
- **Additions:** Real-time streaming with sensors
- **Enhancements:** Incremental dbt for large volumes

### Event Tracking
- **Adapt for:** Application logs, user events, clickstreams
- **Pattern:** High-volume ingestion with partitioning
- **Analytics:** Behavioral analysis, funnel metrics

---

## Demo Data Flow

End-to-end journey of a single glucose reading:

```
1. API Response (Nightscout)
   {"_id": "abc123", "sgv": 145, "date": 1705334400000, ...}

2. DLT Ingestion
   ↓ Fetch from API
   ↓ Validate with Pandera (RawGlucoseEntries)
   ↓ Stage to S3 (Parquet)

3. Iceberg Merge
   ↓ Read from staging
   ↓ Deduplicate by _id
   ↓ Write to dev.glucose_entries

4. dbt Bronze
   ↓ stg_glucose_entries: Clean timestamp, rename fields

5. dbt Silver
   ↓ fct_glucose_readings: Add hour_of_day, glucose_category, is_in_range

6. dbt Gold
   ↓ fct_daily_glucose_metrics: Aggregate daily, calc time_in_range_pct

7. dbt Marts
   ↓ mrt_glucose_overview: Business view for dashboards

8. PostgreSQL Publish
   ↓ Validate with Pandera (FactDailyGlucoseMetrics)
   ↓ Truncate/load to public.mrt_glucose_overview

9. API Exposure
   ├─ PostgREST: GET /mrt_glucose_overview
   ├─ Hasura: GraphQL query
   ├─ Superset: Dashboard chart
   └─ DuckDB: Analyst query
```

**Total time:** ~5 minutes from API to dashboard

---

## Metrics & Impact

### Code Reduction
- **Before:** 270+ lines per ingestion asset
- **After:** ~60 lines with `@phlo_ingestion`
- **Savings:** 78% reduction in boilerplate

### Time to Production
- **Before:** Weeks (manual schema, validation, etc.)
- **After:** Days (declarative pipelines)
- **Speedup:** 10x faster

### Data Quality
- **Before:** Reactive (find issues in production)
- **After:** Proactive (block at source)
- **Impact:** Zero bad data in production

---

## Getting Help

### Documentation
- **Getting Started:** `/docs/getting-started/`
- **Workflow Guide:** `/docs/guides/workflow-development.md`
- **Blog Series:** `/docs/blog/` (12 articles explaining concepts)
- **API Reference:** `/docs/reference/api.md`

### Common Issues
- **Services won't start:** Check `docker compose ps` and logs
- **Ingestion fails:** Verify network access to API, check credentials
- **dbt fails:** Ensure ingestion completed first
- **No API data:** Run publishing step to PostgreSQL

### Example Code
- **Glucose ingestion:** `src/phlo/defs/ingestion/nightscout/glucose.py`
- **Schemas:** `src/phlo/schemas/glucose.py`
- **dbt models:** `transforms/dbt/models/`
- **Analyst queries:** `examples/analyst_duckdb_demo.py`

---

## Next Steps

1. **Try the Quick Start** (15 min)
   - Get hands-on with the platform
   - See data flow end-to-end

2. **Read the Deep Dive** (45 min)
   - Understand architecture decisions
   - Learn best practices

3. **Run the Demo Script** (5 min)
   - Visual walkthrough
   - See all components

4. **Build Your Own**
   - Adapt glucose pattern to your domain
   - Add new data sources
   - Customize transformations

---

## Contributing

Have a demo idea? We'd love to see it!

**Potential demos:**
- Weather data pipeline
- GitHub analytics (already partially implemented!)
- E-commerce transactions
- Social media sentiment
- Financial market data

**To contribute:**
1. Create a new demo following the glucose pattern
2. Include: Quick start + Deep dive + Demo script
3. Add sample data or public API
4. Submit PR with documentation

---

## Resources

### Links
- **Main README:** `/README.md`
- **Package Plan:** `/INSTALLABLE_PACKAGE_PLAN.md`
- **Blog Posts:** `/docs/blog/`
  - 01: Intro to Data Lakehouses
  - 03: Apache Iceberg Explained
  - 05: Data Ingestion with DLT
  - 08: Real-World Example (Glucose)
  - 09: Data Quality with Pandera

### Videos (Coming Soon)
- Platform overview
- Building your first pipeline
- Advanced dbt patterns
- Production deployment

---

**Built with Phlo** - Modern Data Lakehouse Platform

*From complex boilerplate to declarative pipelines in minutes*
