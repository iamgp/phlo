# Cascade Migration: DuckLake → Iceberg + Nessie

## Overview
Complete migration from DuckLake to Apache Iceberg + Project Nessie architecture.
Target: Production-ready, 12-factor stateless design, docker-compose for POC, K8s-ready.

## Architecture Changes

**From:**
- DuckLake (DuckDB + Postgres catalog)
- dbt-duckdb with bootstrap macros
- Custom concurrent write handling

**To:**
- Apache Iceberg (open table format)
- Project Nessie (Git-like catalog with branching)
- Trino (query/compute engine)
- dbt-trino (standard dbt adapter)
- PyIceberg (Python ingestion)
- DuckDB iceberg extension (ad-hoc analysis)

---

## Commit Strategy
- Use conventional commits after each phase
- Format: `type(scope): description`
- Types: `feat`, `refactor`, `chore`, `docs`, `test`
- Example: `feat(infra): add nessie and trino services`

---

## Phase 0: Clean Slate [COMPLETE]

### 0.1 Stop and Remove Everything
- [x] Stop all running services
- [x] Remove all containers
- [x] Remove all volumes (destroys all data)
- [x] Remove orphaned containers/networks
- [x] Clean Python virtual environments

### 0.2 Remove DuckLake Code
- [x] Delete `src/cascade/ducklake/` directory
- [x] Delete `src/cascade/dlt/ducklake_destination.py`
- [x] Delete DuckLake tests: `tests/test_ducklake_integration.py`, `tests/test_concurrent_*.py`
- [x] Delete DuckLake health check: `scripts/check_ducklake_health.py`
- [x] Delete DuckLake-related docs:
  - CONCURRENT_WRITE_DIAGNOSIS.md
  - DIAGNOSIS_SUMMARY.md
  - FIXES.md
  - HONEST_ASSESSMENT.md
  - TEST_RESULTS.md
  - old_spec.md

### 0.3 Clean dbt
- [x] Delete `transforms/dbt/macros/` (DuckLake bootstrap macros)
- [x] Delete `transforms/dbt/target/` (compiled artifacts)
- [x] Keep model structure (will rewrite in Phase 4)

### 0.4 Update Makefile
- [x] Add `make clean-all` target (down -v + system prune)
- [x] Add `make fresh-start` target (clean-all + setup)
- [x] Add profile-specific targets (make up-core, make up-query, make up-all)
- [x] Add Trino/Nessie shell targets
- [x] Add health check target

**Commit:** `chore: clean slate - remove ducklake and all data` (c762d8d)

---

## Phase 1: Infrastructure & Services [COMPLETE]

### 1.1 Nessie Catalog Server
- [x] Add Nessie service to docker-compose.yml
  - Use official projectnessie/nessie Docker image
  - Configure Postgres backend for metadata storage
  - Expose REST API (port 19120)
  - Add healthcheck
  - Create default branches: `main`, `dev`
- [x] Add Nessie to optional profiles (keep core minimal)
- [x] Environment variables: NESSIE_VERSION, NESSIE_PORT

### 1.2 Trino Query Engine
- [x] Add Trino service to docker-compose.yml
  - Use trinodb/trino official image
  - Configure coordinator + worker (single node for POC)
  - Expose port 8080
  - Add healthcheck
- [x] Create Trino catalog configuration directory
  - `docker/trino/catalog/iceberg.properties`
  - Configure Iceberg connector with Nessie REST catalog
  - Configure S3 (MinIO) backend
- [x] Add Trino to optional profiles
- [x] Environment variables: TRINO_VERSION, TRINO_PORT

### 1.3 MinIO Configuration
- [x] Verify existing MinIO setup
- [x] Ensure bucket structure:
  - `lake/warehouse/` (Iceberg tables)
  - `lake/stage/` (raw ingestion landing)
- [x] Update minio-setup service for new buckets

### 1.4 Docker Profiles & 12-Factor Design
- [x] Define docker-compose profiles:
  - `core` (postgres, minio, dagster, hub)
  - `query` (trino, nessie)
  - `bi` (superset, pgweb)
  - `all` (everything)
- [x] Ensure all config via environment variables
- [x] Externalize secrets to .env
- [x] Make services stateless (state only in volumes)

**Commit:** `feat(infra): add nessie and trino services for iceberg architecture` (a16483b)

**Tests:** `tests/test_phase1_infrastructure.sh`

---

## Phase 2: Core Configuration & Secrets [COMPLETE]

### 2.1 Environment Configuration
- [x] Update .env.example with new variables:
  - NESSIE_PORT, NESSIE_VERSION
  - TRINO_PORT, TRINO_VERSION
  - ICEBERG_WAREHOUSE_PATH
- [x] Update cascade/config.py
  - Remove DuckLake configuration
  - Add Nessie, Trino, Iceberg configuration
  - Use Pydantic settings for 12-factor compliance (already using Pydantic)

### 2.2 Docker Compose Environment Variables
- [x] Update dagster-webserver environment variables
  - Remove DUCKLAKE_* variables
  - Add NESSIE_*, TRINO_*, ICEBERG_* variables
- [x] Update dagster-daemon environment variables
  - Remove DUCKLAKE_* variables
  - Add NESSIE_*, TRINO_*, ICEBERG_* variables

### 2.3 Configuration Properties
- [x] Add nessie_uri property to config.py
- [x] Add trino_connection_string property to config.py
- [x] Remove ducklake_data_path property from config.py

**Commit:** `refactor(config): replace ducklake with nessie/trino/iceberg configuration`

**Tests:** `tests/test_phase2_configuration.sh` (21/21 passing)

---

## Phase 3: Ingestion Layer (DLT → PyIceberg) [COMPLETE]

### 3.1 Remove DuckLake Dependencies
- [x] Delete `src/cascade/ducklake/` directory (already removed in Phase 0)
- [x] Delete `src/cascade/dlt/ducklake_destination.py` (already removed in Phase 0)
- [x] Remove DuckLake from pyproject.toml dependencies
  - Removed: duckdb, dbt-duckdb, duckdb-engine, dlt[duckdb]
  - Added: pyiceberg[s3fs,pyarrow], trino, dbt-trino, dlt[parquet]
- [x] Remove DuckLake resource from Dagster (will be removed in Phase 6)

### 3.2 PyIceberg Integration
- [x] Add PyIceberg to dependencies
  - `pyiceberg[s3fs,pyarrow]`
- [x] Create `src/cascade/iceberg/` module
  - `src/cascade/iceberg/__init__.py` - Module exports
  - `src/cascade/iceberg/catalog.py` - Nessie catalog connection with S3/MinIO config
  - `src/cascade/iceberg/tables.py` - Table management (ensure_table, append_to_table)
  - `src/cascade/iceberg/schema.py` - Nightscout schema definitions

### 3.3 Nightscout Ingestion Rewrite
- [x] Update `src/cascade/defs/ingestion/dlt_assets.py`
  - Removed DuckLake destination references
  - Implemented two-step ingestion:
    1. DLT → stage to S3 (parquet files) using filesystem destination
    2. PyIceberg → register/append to Iceberg tables
- [x] Define Iceberg table schemas for Nightscout data
  - Created NIGHTSCOUT_ENTRIES_SCHEMA with all fields
  - Created NIGHTSCOUT_TREATMENTS_SCHEMA for future use
  - Added DLT metadata fields (_dlt_load_id, _dlt_id)
  - Added _cascade_ingested_at timestamp field
- [x] Update entries asset for PyIceberg
  - Uses filesystem destination with parquet format
  - Uses ensure_table() to create/verify table with schema
  - Uses append_to_table() to load data from parquet
  - Handles schema evolution via PyIceberg

### 3.4 Configuration & Staging
- [x] Add staging path configuration
  - Added iceberg_staging_path to config.py (s3://lake/stage)
  - Added ICEBERG_STAGING_PATH to .env.example
  - Created get_staging_path() helper function

### 3.5 Partitioning Strategy
- [x] Define partition specs for Nightscout tables
  - Daily partitions: `day(mills)` for timestamp-based partitioning
  - Partition spec implemented in ensure_table() function
  - Maintains existing daily_partition logic in Dagster

**Commit:** `feat(ingestion): add pyiceberg integration and rewrite dlt assets`

**Tests:** `tests/test_phase3_ingestion.sh` (35/36 passing - import test requires container env)

---

## Phase 4: Transformation Layer (dbt) [COMPLETE]

### 4.1 Remove dbt-duckdb
- [x] Remove dbt-duckdb from dependencies (removed in Phase 3)
- [x] Delete `transforms/dbt/macros/` (already deleted in Phase 0)
- [x] Remove DuckLake-specific dbt hooks
  - Removed on-run-start: ducklake__bootstrap()
  - Removed pre-hook: ducklake__bootstrap()
  - Removed macro-paths reference

### 4.2 Install dbt-trino
- [x] Add dbt-trino to `services/dagster/pyproject.toml` (added in Phase 3)
- [x] Installed via uv workspace sync

### 4.3 Update dbt Configuration
- [x] Rewrite `transforms/dbt/profiles/profiles.yml`
  - Added dev/prod Trino outputs with Nessie branching
  - dev target uses nessie.reference: dev
  - prod target uses nessie.reference: main
  - Kept postgres output for marts
  - Removed all duckdb configuration

- [x] Update `transforms/dbt/dbt_project.yml`
  - Removed on-run-start hooks
  - Removed pre-hooks
  - Removed macro-paths
  - Kept bronze/silver/gold/marts_postgres structure
  - Default materialization: table (Iceberg tables)

### 4.4 Rewrite dbt Models for Iceberg
- [x] Update source definitions (`transforms/dbt/models/sources/sources.yml`)
  - Point to Iceberg raw tables via Trino catalog
  - database: iceberg, schema: raw
- [x] Rewrite bronze models (stg_entries.sql)
  - Replaced epoch_ms() with from_unixtime(mills / 1000.0)
  - Updated to read from Iceberg raw.entries
  - Trino-compatible date functions
- [x] Rewrite silver models (fct_glucose_readings.sql)
  - Replaced dayname() with format_datetime()
  - Replaced extract(dow) with day_of_week()
  - Replaced extract(epoch...) with date_diff('minute',...)
  - Iceberg table materialization
- [x] Rewrite gold models
  - dim_date.sql: week(), month(), year(), format_datetime()
  - mrt_glucose_readings.sql: incremental Iceberg table
- [x] Update marts_postgres models
  - mrt_glucose_overview.sql: Trino interval syntax
  - mrt_glucose_hourly_patterns.sql: approx_percentile() instead of percentile_cont()

### 4.5 SQL Function Migrations
- [x] DuckDB → Trino function replacements:
  - epoch_ms(date) → from_unixtime(cast(mills as double) / 1000.0)
  - dayname() → format_datetime(timestamp, 'EEEE')
  - extract(dow) → day_of_week()
  - extract(week) → week()
  - extract(epoch from interval) → date_diff('minute', start, end)
  - percentile_cont() → approx_percentile()
  - interval '90 days' → interval '90' day

**Commit:** `refactor(dbt): migrate from dbt-duckdb to dbt-trino with iceberg`

**Tests:** `tests/test_phase4_transformation.sh` (32/32 passing)

---

## Phase 5: Publishing & BI [COMPLETE]

### 5.1 Postgres Marts Publishing
- [x] Strategy: Use Dagster asset approach (Trino → Postgres)
- [x] Delete duckdb_to_postgres.py
- [x] Create trino_to_postgres.py
  - Queries mart tables from Iceberg via Trino
  - Publishes to Postgres using psycopg2 for BI/Superset
  - Handles iceberg.marts.mrt_glucose_overview
  - Handles iceberg.marts.mrt_glucose_hourly_patterns
- [x] Update publishing/__init__.py imports

### 5.2 Docker Compose Configuration
- [x] Add ICEBERG_STAGING_PATH to dagster-webserver environment
- [x] Add ICEBERG_STAGING_PATH to dagster-daemon environment
- [x] Verify all Trino/Iceberg env vars present

### 5.3 Publishing Strategy
Publishing follows a two-tier architecture:
1. **Iceberg (via Trino)**: Analytical lakehouse layer
   - Bronze/silver/gold schemas in Iceberg
   - Queried via Trino for transformations
2. **Postgres**: Fast query layer for BI
   - Marts schema with curated tables
   - Published from Iceberg via Dagster asset
   - Superset queries Postgres for dashboards

Note: Superset Trino configuration deferred to operational phase

**Commit:** `refactor(publishing): migrate from duckdb to trino/postgres publishing`

**Tests:** `tests/test_phase5_publishing.sh` (all passing)

---

## Phase 6: Orchestration (Dagster)

### 6.1 Remove DuckLake Resources
- [ ] Delete `src/cascade/defs/resources/ducklake.py`
- [ ] Remove DuckLake resource from `src/cascade/defs/resources/__init__.py`

### 6.2 Add Trino & PyIceberg Resources
- [ ] Create `src/cascade/defs/resources/trino.py`
  - Trino connection resource (using trino-python-client)
- [ ] Create `src/cascade/defs/resources/iceberg.py`
  - PyIceberg catalog resource
  - Configure Nessie REST catalog URI
  - S3/MinIO configuration
- [ ] Update `src/cascade/defs/resources/__init__.py`

### 6.3 Update Dagster Assets
- [ ] Rewrite ingestion assets (`src/cascade/defs/ingestion/`)
  - nightscout_raw → nightscout_raw_iceberg
  - Use PyIceberg for table registration/append
- [ ] Update transform assets (`src/cascade/defs/transform/dbt.py`)
  - Update dbt resource configuration for dbt-trino
  - Ensure dbt runs target `dev` or `prod` profiles
- [ ] Update publishing assets (`src/cascade/defs/publishing/`)
  - Trino → Postgres mart publishing
- [ ] Update quality checks (`src/cascade/defs/quality/`)
  - Pandera validation on Iceberg tables (via Trino or PyIceberg)

### 6.4 Asset Dependencies & Lineage
- [ ] Update asset dependency graph
  - nightscout_raw_iceberg → dbt bronze → dbt silver → dbt gold → postgres marts
- [ ] Ensure partition-aware dependencies
- [ ] Test full pipeline execution

### 6.5 Schedules & Sensors
- [ ] Update `src/cascade/defs/schedules/pipeline.py`
  - Daily ingestion schedule
  - dbt transformation schedule
  - Mart publishing schedule

---

## Phase 7: Nessie Branching Workflow

### 7.1 Branch Management
- [ ] Create Dagster assets/ops for Nessie branch operations
  - Create branch
  - Merge branch
  - List branches
  - Tag snapshot
- [ ] Document dev → main promotion workflow
  - Run dbt on `dev` branch
  - Validate in Superset
  - Merge `dev` → `main` via Nessie API

### 7.2 CI/CD Integration (Future)
- [ ] Document how to run dbt tests on `dev` branch
- [ ] Document merge approval workflow
- [ ] Atomic publish via Nessie merge

---

## Phase 8: Testing & Validation

### 8.1 Integration Tests
- [ ] Test end-to-end pipeline
  - Nightscout API → Iceberg raw table
  - dbt build on Trino
  - Postgres marts populated
  - Superset queries work
- [ ] Test partitioning
  - Multi-day ingestion
  - Partition pruning in Trino
- [ ] Test time travel
  - Query historical snapshots via Trino
  - Iceberg snapshot API

### 8.2 Nessie Workflow Test
- [ ] Create `dev` branch
- [ ] Run dbt on `dev`
- [ ] Validate changes
- [ ] Merge `dev` → `main`
- [ ] Verify atomic commit

### 8.3 Concurrency Tests
- [ ] Test concurrent writes to different partitions (Iceberg ACID)
- [ ] Verify no catalog lock issues (Nessie advantage over DuckLake)

---

## Phase 9: DuckDB Iceberg Extension (Ad-hoc Analysis)

### 9.1 DuckDB Setup Instructions
- [ ] Create documentation: `docs/duckdb-iceberg-queries.md`
- [ ] Install DuckDB locally
- [ ] Install iceberg extension
- [ ] Configure S3 credentials
- [ ] Example queries:
  ```sql
  INSTALL iceberg;
  LOAD iceberg;

  -- Configure S3 (MinIO)
  SET s3_endpoint = 'localhost:9000';
  SET s3_use_ssl = false;
  SET s3_url_style = 'path';
  SET s3_access_key_id = 'your-key';
  SET s3_secret_access_key = 'your-secret';

  -- Query Iceberg table
  SELECT * FROM iceberg_scan('s3://lake/warehouse/raw/entries');
  ```

### 9.2 DuckDB Integration in Hub (Optional)
- [ ] Add DuckDB query interface to Hub app
- [ ] Pre-configured connection to Iceberg tables
- [ ] Read-only access for analysts

---

## Phase 10: Documentation & Cleanup

### 10.1 Architecture Documentation
- [ ] Update README.md
  - Replace DuckLake with Iceberg+Nessie architecture
  - Update architecture diagram (Mermaid)
  - Update component descriptions
- [ ] Create ARCHITECTURE.md
  - Detailed Iceberg+Nessie design
  - Data flow diagrams
  - Service dependencies

### 10.2 Setup & Operations
- [ ] Update QUICK_START.md
  - New service startup instructions
  - Docker profile usage
  - Nessie branch setup
- [ ] Create NESSIE_WORKFLOW.md
  - Branching best practices
  - Dev → main promotion
  - Time travel queries

### 10.3 Migration Notes
- [ ] Create MIGRATION_FROM_DUCKLAKE.md
  - Why we migrated
  - Key differences
  - What was removed
  - Breaking changes

### 10.4 Cleanup Old Files
- [ ] Delete DuckLake-related documentation
  - CONCURRENT_WRITE_DIAGNOSIS.md
  - DIAGNOSIS_SUMMARY.md
  - FIXES.md
  - HONEST_ASSESSMENT.md
  - TEST_RESULTS.md
- [ ] Archive old_spec.md
- [ ] Clean up any DuckLake test files

---

## Phase 11: Production Hardening

### 11.1 Observability
- [ ] Add Trino metrics endpoint
- [ ] Add Nessie health checks
- [ ] Dagster sensor for pipeline failures
- [ ] Logging configuration (structured logs)

### 11.2 Security
- [ ] Secure Nessie API (authentication)
- [ ] Secure Trino (LDAP/Kerberos for production)
- [ ] MinIO bucket policies
- [ ] Secret management (Docker secrets / K8s secrets)

### 11.3 Backup & Recovery
- [ ] Nessie metadata backup strategy (Postgres dumps)
- [ ] Iceberg snapshot retention policies
- [ ] MinIO versioning/replication

### 11.4 K8s Readiness
- [ ] Helm chart structure planning
- [ ] StatefulSets for Nessie/Trino
- [ ] PersistentVolumeClaims for volumes
- [ ] ConfigMaps for configuration
- [ ] Secrets management

---

## Success Criteria

### POC Outcomes (from spec)
1. [ ] End-to-end load: Nightscout → Iceberg on MinIO (daily partitions)
2. [ ] dbt builds/updates Iceberg models via Trino
3. [ ] Nessie branch workflow (dev → main) + time-travel query
4. [ ] Curated marts published to Postgres for Superset

### Production Ready
- [ ] All services run via docker-compose with profiles
- [ ] Complete asset-based pipeline in Dagster
- [ ] dbt bronze/silver/gold/marts models working
- [ ] Superset dashboards functional
- [ ] Documentation complete
- [ ] Tests passing
- [ ] 12-factor compliant (K8s-ready)

---

## Dependencies & Prerequisites

### Docker Images
- `projectnessie/nessie:latest`
- `trinodb/trino:latest`
- `minio/minio:RELEASE.2025-09-07T16-13-09Z` (existing)
- PostgreSQL (existing)

### Python Packages
- `pyiceberg[s3fs,pyarrow]`
- `dbt-trino`
- `trino-python-client`
- `dlt[parquet]` (existing)
- Remove: `duckdb`, `dlt-ducklake`, `dbt-duckdb`

### External Services
- MinIO (existing)
- Postgres (existing)

---

## Estimated Effort

- **Phase 1-2 (Infrastructure):** 1 day
- **Phase 3 (Ingestion):** 1 day
- **Phase 4 (dbt):** 1 day
- **Phase 5-6 (Publishing/Dagster):** 1 day
- **Phase 7-8 (Nessie/Testing):** 0.5 day
- **Phase 9-10 (Docs/Cleanup):** 0.5 day
- **Phase 11 (Hardening):** 1 day

**Total: ~6 days** (focused work, as per spec's 2-3 day POC + production hardening)

---

## Notes

- This is a **complete rewrite**, not a migration. No DuckLake backwards compatibility.
- Keep existing Dagster/Superset/MinIO/Postgres infrastructure.
- Focus on stateless, 12-factor design for easy K8s migration.
- Use docker-compose profiles to keep core minimal.
- Nightscout API is the only data source for now.
