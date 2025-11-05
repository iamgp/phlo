# Cascade Lakehouse Platform - Complete Repository Overview

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Data Flow](#data-flow)
5. [Core Components](#core-components)
6. [Configuration](#configuration)
7. [Tech Stack](#tech-stack)
8. [Getting Started](#getting-started)
9. [Key Design Patterns](#key-design-patterns)

---

## Project Overview

**Cascade** is a production-ready, open-source data lakehouse platform built on Apache Iceberg and Project Nessie. It provides a complete, integrated solution for modern data engineering.

### Key Capabilities

- **Git-like version control for data** - Branching, tagging, merging with atomic commits
- **ACID transactions** - Data integrity guarantees across operations
- **Time travel queries** - Query data as it existed at any point in history
- **Multi-engine analytics** - Query with Trino, DuckDB, or other engines
- **Asset-based orchestration** - Declarative data pipelines with automatic lineage
- **BI dashboarding** - Built-in analytics and visualization (Superset)
- **REST and GraphQL APIs** - Programmatic data access with authentication
- **Complete observability** - Metrics, logs, and dashboards (Prometheus, Grafana, Loki)

### Example Use Case

The project includes a complete **Nightscout CGM (glucose monitoring) data pipeline** demonstrating:
- Ingestion from external APIs (Nightscout, GitHub)
- Bronze/Silver/Gold data layering
- Transformations and metrics
- Publication to BI systems

---

## Architecture

### High-Level Design Pattern: Lakehouse Architecture

```
DATA SOURCES → INGESTION → STORAGE (ICEBERG) → TRANSFORM (dbt) → PUBLISH → ANALYTICS
```

### Core Components

#### Storage Layer
- **Apache Iceberg** - Open table format providing ACID, schema evolution, time travel
- **Project Nessie** - Git-like catalog enabling branching, versioning, atomic commits
- **MinIO** - S3-compatible object storage for data files and metadata
- **PostgreSQL** - Relational database for service metadata and analytics marts

#### Compute Layer
- **Trino** - Distributed SQL query engine for analytics and transformations
- **dbt** - SQL-based data transformations and modeling (bronze/silver/gold layers)
- **DuckDB** - Ad-hoc analytical queries (via Iceberg extension)

#### Orchestration
- **Dagster** - Asset-based orchestration with lineage tracking and scheduling
- **Dagster Sensors & Schedules** - Automated pipeline triggers

#### APIs
- **FastAPI** - REST API with JWT authentication, rate limiting, caching
- **Hasura** - Auto-generated GraphQL API with subscriptions

#### Analytics & BI
- **Superset** - Business intelligence dashboards
- **Flask Hub** - Service discovery dashboard

#### Observability
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and alerting
- **Loki** - Centralized log aggregation
- **Grafana Alloy** - Telemetry collector

---

## Directory Structure

```
cascade/
├── src/cascade/                        # Main Python package
│   ├── config.py                       # Centralized configuration (pydantic-settings)
│   ├── definitions.py                  # Main Dagster entry point (merges all defs)
│   │
│   ├── defs/                           # Dagster asset definitions
│   │   ├── ingestion/                  # Raw data ingestion layer
│   │   │   ├── dlt_assets.py           # Nightscout/DLT glucose entries
│   │   │   └── github_assets.py        # GitHub user events & repo stats
│   │   │
│   │   ├── transform/                  # Transformation assets
│   │   │   └── dbt.py                  # dbt integration
│   │   │
│   │   ├── publishing/                 # Publishing to PostgreSQL
│   │   │   ├── trino_to_postgres.py    # Iceberg → Postgres marts
│   │   │   └── config.yaml             # Publishing configurations
│   │   │
│   │   ├── quality/                    # Data quality checks
│   │   ├── nessie/                     # Git-like branching operations
│   │   ├── resources/                  # External service integrations
│   │   ├── schedules/                  # Scheduled triggers
│   │   └── sensors/                    # Event-based triggers
│   │
│   ├── iceberg/                        # PyIceberg catalog utilities
│   │   ├── catalog.py                  # Catalog connection & listing
│   │   ├── tables.py                   # Table operations
│   │   └── schema.py                   # Schema definitions
│   │
│   └── schemas/                        # Pandera data validation schemas
│
├── services/                           # Microservices
│   ├── api/                            # FastAPI REST service
│   │   └── app/
│   │       ├── main.py                 # FastAPI entry point
│   │       ├── routers/                # API endpoints
│   │       ├── middleware/             # Auth, rate limiting, caching
│   │       ├── connectors/             # Trino & Postgres connections
│   │       └── auth/                   # JWT authentication
│   │
│   ├── hub/                            # Flask dashboard service
│   ├── dagster/                        # Dagster environment
│   └── superset/                       # Superset BI configuration
│
├── transforms/dbt/                     # dbt data transformation models
│   ├── models/
│   │   ├── sources/                    # Source definitions
│   │   ├── bronze/                     # Staging layer
│   │   ├── silver/                     # Fact tables
│   │   ├── gold/                       # Dimension tables
│   │   └── marts_postgres/             # Business metrics for BI
│   │
│   └── dbt_project.yml                 # dbt configuration
│
├── docker/                             # Docker service configurations
│   ├── Dockerfile.*                    # Service-specific Dockerfiles
│   ├── postgres/                       # PostgreSQL init scripts
│   ├── minio/                          # MinIO bucket setup
│   ├── trino/                          # Trino catalog configs
│   ├── prometheus/                     # Prometheus scrape configs
│   └── grafana/                        # Grafana dashboards
│
├── docs/                               # Documentation
├── tests/                              # Test suite
├── examples/                           # Example configurations
├── docker-compose.yml                  # Complete service orchestration
├── Makefile                            # Development shortcuts
└── pyproject.toml                      # Python project configuration
```

### Key Module Organization

**src/cascade/defs/** - Modular Dagster definitions:
- Each subdirectory has `__init__.py` with `build_defs()` returning `dg.Definitions`
- Main `definitions.py` merges all submodule definitions
- Executor selection based on platform (Linux multiprocess, macOS in-process)

**src/cascade/iceberg/** - PyIceberg utilities:
- `catalog.py` - Nessie REST catalog connection
- `tables.py` - Table operations (ensure, append, delete)
- `schema.py` - Schema definitions for glucose and GitHub data

**services/** - Microservices:
- Each service has its own Docker configuration
- FastAPI service includes authentication, routing, middleware
- Hub provides visual service discovery and status

---

## Data Flow

### End-to-End Pipeline Flow

#### 1. INGESTION LAYER
```
DLT fetches data from external APIs
├─ Nightscout API → entries (glucose readings)
└─ GitHub API → user_events, repo_stats

Data staging to S3 (MinIO) as Parquet files

PyIceberg registers/appends to Iceberg tables
├─ raw.glucose_entries
├─ raw.github_user_events
└─ raw.github_repo_stats
```

#### 2. CATALOG LAYER (Nessie)
```
Maintains table metadata and versions
├─ Supports branching (dev/main)
├─ Tracks snapshots for time travel
└─ Provides REST API for catalog operations
```

#### 3. TRANSFORMATION LAYER (dbt + Trino)
```
BRONZE LAYER (Staging):
├─ stg_glucose_entries - type conversions, cleaning
├─ stg_github_user_events - standardization
└─ stg_github_repo_stats - normalization

SILVER LAYER (Facts):
├─ fct_glucose_readings - calculated metrics, aggregations
└─ fct_github_* - derived fact tables

GOLD LAYER (Dimensions):
├─ dim_date - date dimension table
└─ Other conformed dimensions

MARTS LAYER:
├─ mrt_glucose_overview - glucose analytics
└─ mrt_github_activity - GitHub metrics
```

#### 4. PUBLISHING LAYER
```
Trino queries gold/marts from Iceberg
├─ Results inserted into PostgreSQL marts schema
└─ Creates optimized tables for BI tools
```

#### 5. ANALYTICS LAYER
```
Superset connects to:
├─ PostgreSQL marts (fast, indexed)
└─ Trino (ad-hoc analysis on Iceberg)

Dashboards visualize metrics
Users explore data
```

#### 6. API LAYERS
```
FastAPI REST:
├─ JWT authentication (admin/analyst roles)
├─ Query Iceberg via Trino
├─ Access Postgres marts
└─ Rate limiting & caching

Hasura GraphQL:
├─ Auto-generated from Postgres schema
└─ Real-time subscriptions
```

### Data Branching with Nessie

```
MAIN BRANCH (Production)
├─ raw.glucose_entries (snapshot_id: xyz000)
├─ bronze.stg_entries (snapshot_id: uvw111)
└─ silver.fct_glucose_readings (snapshot_id: rst222)

DEV BRANCH (Development)
├─ raw.glucose_entries (snapshot_id: abc123) [newer data]
├─ bronze.stg_entries (snapshot_id: def456)
└─ silver.fct_glucose_readings (snapshot_id: ghi789)

PROMOTION WORKFLOW:
1. Ingest daily data to dev branch
2. Transform with dbt on dev
3. Validate data quality
4. Merge dev → main (atomic, multi-table)
5. Publish main to PostgreSQL marts
```

### Orchestration Flow (Dagster)

**Asset Dependency Graph:**
```
nightscout_api (external)
  ↓ [DLT ingestion]
entries (dlt_glucose_entries)
  ↓ [dbt dependencies]
dbt:bronze.stg_glucose_entries
  ↓
dbt:silver.fct_glucose_readings
  ↓
dbt:gold.dim_date
  ↓ [Nessie branch promotion]
promote_dev_to_main
  ↓ [Publishing]
postgres_glucose_marts
  ↓ [External]
superset_dashboards
```

**Execution:**
- Dagster detects asset materializations and dependencies
- Sensors monitor for changes
- Schedules trigger runs (daily at 2 AM)
- Each asset materializes independently with partitioning support
- Failures trigger retry logic and monitoring

---

## Core Components

### Entry Points

#### 1. Main Dagster Entry Point
**File:** `src/cascade/definitions.py`

```python
# Merges all modular definitions
def _merged_definitions() -> dg.Definitions:
    merged = dg.Definitions.merge(
        build_resource_defs(),      # trino, iceberg, dbt resources
        build_ingestion_defs(),     # DLT assets (entries, github_*)
        build_transform_defs(),     # dbt assets
        build_publishing_defs(),    # Postgres publication
        build_quality_defs(),       # Data quality checks
        build_nessie_defs(),        # Branch management
        build_schedule_defs(),      # Schedules & sensors
        build_sensor_defs(),        # Event triggers
    )
```

#### 2. REST API Entry Point
**File:** `services/api/app/main.py`

```python
# FastAPI app setup
app = FastAPI(title="Cascade Lakehouse API", ...)

# Middleware
app.add_exception_handler(RateLimitExceeded, ...)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(glucose.router, prefix="/api/v1")
app.include_router(iceberg.router, prefix="/api/v1")
```

**Port:** 10010 (default)
**Features:** JWT authentication, rate limiting, caching, Prometheus metrics

#### 3. Hub Dashboard Entry Point
**File:** `services/hub/app.py`

**Port:** 10009 (default)
**Purpose:** Service discovery, quick links to all platform services

### Asset Materialization Flow

#### Ingestion Asset Example (DLT)

```python
@dg.asset(
    name="dlt_glucose_entries",
    partitions_def=daily_partition,
    automation_condition=dg.AutomationCondition.on_cron("0 */1 * * *"),
)
def entries(context, iceberg: IcebergResource) -> dg.MaterializeResult:
    # 1. Fetch from Nightscout API
    # 2. Stage to S3 (MinIO) as Parquet
    # 3. Register in Iceberg raw.glucose_entries
    # 4. Update Nessie catalog
    # 5. Return materialization result
```

#### Transform Asset Example (dbt)

```python
@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    partitions_def=daily_partition,
)
def all_dbt_assets(context, dbt: DbtCliResource):
    # 1. Run dbt build (compile → execute)
    # 2. Read Iceberg tables (raw layer)
    # 3. Write transformation results (bronze/silver/gold)
    # 4. Generate dbt docs
    # 5. Update Dagster with lineage
```

#### Publishing Asset Example

```python
@asset(deps=["dbt:*"])
def postgres_glucose_marts(context, trino: TrinoResource):
    # 1. Query gold/marts from Iceberg via Trino
    # 2. Connect to PostgreSQL
    # 3. Drop existing mart tables
    # 4. Insert query results
    # 5. Commit transaction
```

---

## Configuration

### Centralized Configuration System

**Location:** `src/cascade/config.py`

**Method:** Pydantic Settings with environment variables and `.env` file

### Key Settings

#### Database - PostgreSQL
```
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
POSTGRES_MART_SCHEMA (default: "marts")
```

#### Storage - MinIO
```
MINIO_HOST, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
MINIO_API_PORT, MINIO_CONSOLE_PORT
```

#### Catalog - Nessie
```
NESSIE_VERSION, NESSIE_PORT, NESSIE_HOST
```

#### Query Engine - Trino
```
TRINO_VERSION, TRINO_PORT, TRINO_HOST, TRINO_CATALOG
```

#### Data Lake - Iceberg
```
ICEBERG_WAREHOUSE_PATH (s3://lake/warehouse)
ICEBERG_STAGING_PATH (s3://lake/stage)
ICEBERG_DEFAULT_NAMESPACE (raw)
ICEBERG_NESSIE_REF (dev/main branch)
```

#### Orchestration - Dagster
```
DAGSTER_PORT
CASCADE_FORCE_IN_PROCESS_EXECUTOR
CASCADE_FORCE_MULTIPROCESS_EXECUTOR
```

#### BI Services - Superset
```
SUPERSET_PORT, SUPERSET_ADMIN_USER, SUPERSET_ADMIN_PASSWORD
```

#### APIs
```
API_PORT, JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
HASURA_PORT, HASURA_ADMIN_SECRET
```

#### GitHub Integration
```
GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_BASE_URL
```

#### Observability
```
PROMETHEUS_PORT, LOKI_PORT, GRAFANA_PORT, ALLOY_PORT
```

### Features
- `@computed_field` properties for derived paths
- Helper methods: `get_pyiceberg_catalog_config()`, `get_postgres_connection_string()`
- `@lru_cache` for single config instance
- 12-factor compliant (stateless, env-based)

**Configuration File:** `.env` (example provided in `.env.example`)

---

## Tech Stack

### Core Technologies

#### Table Format & Catalog
- Apache Iceberg (0.x) - Open table format
- Project Nessie (0.105.5+) - Git-like versioning

#### Storage
- MinIO (S3-compatible) - Object storage
- PostgreSQL (13+) - Relational database

#### Query Engines
- Trino (477+) - Distributed SQL engine
- dbt-trino - dbt adapter for Trino
- DuckDB (optional) - Local analytical queries

#### Orchestration
- Dagster - Asset orchestration platform
- dagster-dbt - dbt integration
- dagster-pandera - Data quality checks
- DLT (Data Load Tool) - Reliable data loading

#### APIs
- FastAPI - Modern Python web framework
- Hasura - GraphQL engine
- Pydantic - Data validation

#### BI & Visualization
- Apache Superset - Business intelligence
- Grafana - Dashboards & alerts
- Prometheus - Metrics collection
- Loki - Log aggregation

### Key Python Packages

From `pyproject.toml`:
```
dagster, dagster-webserver, dagster-postgres, dagster-aws, dagster-dbt, dagster-pandera
dbt-core, dbt-postgres
pydantic-settings, pydantic
dlt, pyiceberg[s3fs,pyarrow], pandas
pandera (data validation)
trino, requests, psycopg2-binary
ruff, basedpyright (dev tools)
pytest (testing)
```

### Docker Compose Services

```
postgres, minio, nessie, trino
dagster-webserver, dagster-daemon
superset, pgweb, hub, api, hasura
prometheus, loki, alloy, grafana
mkdocs
```

---

## Getting Started

### Service Startup Order

#### Phase 1: Foundation
```bash
docker-compose up postgres minio    # Wait for health checks
```

#### Phase 2: Catalog
```bash
docker-compose up nessie            # Depends on postgres, minio
docker-compose up nessie-setup      # Create branches
```

#### Phase 3: Compute
```bash
docker-compose up trino             # Depends on nessie, minio
```

#### Phase 4: Orchestration
```bash
docker-compose up dagster-webserver dagster-daemon
```

#### Phase 5: Optional Services
```bash
docker-compose up superset hub api hasura
docker-compose up prometheus loki grafana
```

### Makefile Commands

```bash
make up-core              # postgres, minio, dagster
make up-query             # nessie, trino
make up-bi                # superset, pgweb
make up-api               # rest api, graphql
make up-observability     # prometheus, grafana, loki
make up-all               # Everything
```

### Access Points

After startup, services are available at:

- **Dagster UI:** http://localhost:3000
- **Hub Dashboard:** http://localhost:10009
- **REST API:** http://localhost:10010
- **Superset:** http://localhost:10008
- **Trino:** http://localhost:10011
- **Grafana:** http://localhost:10003
- **Prometheus:** http://localhost:10000

---

## Key Design Patterns

### 1. Modular Definitions Pattern

**Decision:** Split Dagster definitions across modules with `build_defs()` functions

**Benefit:**
- Each module independently importable and testable
- Easy to enable/disable features
- Clear separation of concerns
- Scalable to many assets

### 2. Branch-Aware Catalog Pattern

**Decision:** Use Nessie branches (dev/main) with separate Trino catalogs

**Benefit:**
- Dev and prod data isolated
- Safe testing without affecting production
- Atomic promotion (merge dev → main)
- Time travel to historical states

### 3. DLT + PyIceberg Two-Step Ingestion

**Decision:** Stage to S3 first, then register with PyIceberg

**Benefit:**
- Reliable, testable data loading (DLT responsibility)
- Atomic table registration (PyIceberg responsibility)
- Separation of concerns
- Can re-run registration without re-fetching

### 4. Custom dbt Translator

**Decision:** Map dbt resources to Dagster assets with workflow-based grouping

**Benefit:**
- Models grouped by workflow (nightscout, github) not just layer
- DLT assets properly linked as dbt sources
- Automatic lineage from dbt to Iceberg

### 5. Resource-Based Dependency Injection

**Decision:** Use Dagster `@resource` pattern for external services

**Benefit:**
- Loose coupling between assets and services
- Easy to mock for testing
- Configuration centralized in one place
- Consistent API across services

### 6. Partition-Aware Asset Dependencies

**Decision:** Use daily partitions across ingestion and transformation

**Benefit:**
- Incremental processing (only latest day)
- Automatic partition matching
- Easy to backfill missing partitions
- Clear temporal semantics

### 7. Stateless Service Architecture

**Decision:** All state in PostgreSQL, MinIO, or Iceberg (never in container)

**Benefit:**
- Services can be restarted without data loss
- Horizontal scaling possible
- 12-factor compliance
- Cloud-native ready

### 8. Multiple API Layers

**Decision:** Both REST (FastAPI) and GraphQL (Hasura)

**Benefit:**
- REST for simple, standard workflows
- GraphQL for flexible queries
- Hasura auto-generates from Postgres schema
- JWT tokens work for both

### 9. Comprehensive Testing Layers

**Decision:** Unit tests (Python), integration tests (shell), end-to-end tests

**Benefit:**
- Phase-based testing (infrastructure → ingestion → transform → publish)
- Easy to diagnose failures
- Can validate each layer independently

### 10. Observability-First Design

**Decision:** Full stack: Prometheus metrics, Loki logs, Grafana dashboards

**Benefit:**
- Understand what's happening in real-time
- Alert on anomalies
- Historical investigation capability
- Multi-layer metrics (service, pipeline, query)

---

## Summary

**Cascade** is a sophisticated, production-grade data lakehouse platform that elegantly combines:

1. **Modern table format** (Iceberg) with Git-like versioning (Nessie)
2. **Modular orchestration** (Dagster) with clear asset lineage
3. **Multi-layer transformations** (dbt: bronze/silver/gold/marts)
4. **Flexible access** (REST API, GraphQL, direct SQL)
5. **Comprehensive observability** (metrics, logs, dashboards)
6. **Cloud-native architecture** (stateless, containerized, portable)

The codebase demonstrates **excellent software engineering practices**: modular design, configuration management, resource injection, comprehensive testing, and clear separation of concerns. It's suitable as both a production system and a learning resource for modern data engineering patterns.

---

## Additional Resources

- **Architecture Details:** See `docs/architecture.md`
- **API Documentation:** See `docs/API.md`
- **Quick Start Guide:** See `docs/quick-start.md`
- **Observability Guide:** See `docs/OBSERVABILITY.md`
- **Configuration Guide:** See `docs/configuration.md`

---

*Generated on 2025-11-05*
