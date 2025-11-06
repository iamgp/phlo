# Cascade Documentation

Welcome to the Cascade documentation. This guide will help you understand, deploy, and use the Cascade data lakehouse platform.

## 📖 **START HERE: [Documentation Index](INDEX.md)**

**New to Cascade?** Check out the **[INDEX.md](INDEX.md)** for a complete guide to all documentation, organized by experience level and topic.

---

## Quick Navigation

### 🚀 Complete Beginners

**Start with these comprehensive guides:**

1. **[BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md)** - **Start here!**
   - What is a data lakehouse?
   - All concepts explained from scratch
   - How Cascade works end-to-end
   - Understanding the technologies
   - Your first look at the platform

2. **[WORKFLOW_DEVELOPMENT_GUIDE.md](WORKFLOW_DEVELOPMENT_GUIDE.md)**
   - Complete tutorial: Build a weather pipeline
   - Step-by-step from zero to production
   - Uses DLT, dbt, Bronze/Silver/Gold layers
   - 10-step guided walkthrough

3. **[Quick Start Guide](../QUICK_START.md)** - Get Cascade running
   - Prerequisites and setup
   - Service startup
   - First pipeline run

### 👨‍💻 For Developers

If you're developing on Cascade:

1. **[DATA_MODELING_GUIDE.md](DATA_MODELING_GUIDE.md)** - Architecture patterns
   - Bronze/Silver/Gold explained
   - Fact vs dimension tables
   - Real-world examples

2. **[DAGSTER_ASSETS_TUTORIAL.md](DAGSTER_ASSETS_TUTORIAL.md)** - Orchestration
   - Complete assets guide
   - Dependencies, resources, partitions
   - Schedules and sensors

3. **[DBT_DEVELOPMENT_GUIDE.md](DBT_DEVELOPMENT_GUIDE.md)** - Transformations
   - dbt fundamentals
   - Models, tests, documentation
   - Incremental models

### 🔧 For Data Engineers

If you're building pipelines on Cascade:

1. **[BEST_PRACTICES_GUIDE.md](BEST_PRACTICES_GUIDE.md)** - Production patterns
   - Code organization
   - Data quality
   - Performance & security

2. **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)** - Fix issues
   - Services won't start
   - Dagster/dbt problems
   - Debugging techniques

3. **[Nessie Workflow Guide](../NESSIE_WORKFLOW.md)** - Branching and promotion
   - Branch management (dev/main)
   - Merge workflows
   - Time travel queries

4. **[DuckDB Query Guide](./duckdb-iceberg-queries.md)** - Ad-hoc analysis
   - DuckDB setup
   - Query examples
   - Python integration

5. **[OpenMetadata Setup](./OPENMETADATA_SETUP.md)** - Data catalog and discovery
   - Self-service data discovery
   - Metadata management
   - Data lineage visualization
   - Search and documentation

## Documentation Structure

### Root-Level Guides

- **[README.md](../README.md)** - Main project overview
  - Architecture summary
  - Quick start instructions
  - Key features
  - Troubleshooting

- **[QUICK_START.md](../QUICK_START.md)** - Setup and first steps
  - Installation
  - Service startup
  - First pipeline run
  - Common tasks

- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Detailed system design
  - Component architecture
  - Data flow
  - Service dependencies
  - Performance and security

- **[NESSIE_WORKFLOW.md](../NESSIE_WORKFLOW.md)** - Branching guide
  - Branch management
  - Dev → main promotion
  - Time travel
  - Advanced workflows

### docs/ Directory

- **[duckdb-iceberg-queries.md](./duckdb-iceberg-queries.md)** - DuckDB analysis guide
  - Installation and setup
  - Query examples
  - Python integration
  - Troubleshooting

## Core Concepts

### Apache Iceberg

Iceberg is an open table format for large analytic datasets. Key features:

- **ACID Transactions**: Atomic commits prevent data corruption
- **Schema Evolution**: Add/remove columns without rewrites
- **Hidden Partitioning**: Partition pruning without manual filtering
- **Time Travel**: Query data as it existed at any point
- **Snapshot Isolation**: Readers never block writers

**Learn more**: [ARCHITECTURE.md - Apache Iceberg](../ARCHITECTURE.md#1-apache-iceberg-table-format)

### Project Nessie

Nessie provides Git-like version control for data tables. Key features:

- **Branching**: Isolate dev/staging/prod environments
- **Atomic Commits**: Update multiple tables together
- **Merge Operations**: Promote changes atomically
- **Time Travel**: Query any historical state
- **Tags**: Mark releases for reproducibility

**Learn more**: [NESSIE_WORKFLOW.md](../NESSIE_WORKFLOW.md)

### Trino

Trino is a distributed SQL query engine. Key features:

- **Native Iceberg Support**: First-class connector
- **Distributed Execution**: Scale to large datasets
- **Push-down Optimization**: Leverage Iceberg metadata
- **Session Properties**: Control branch selection

**Learn more**: [ARCHITECTURE.md - Trino](../ARCHITECTURE.md#3-trino-query-engine)

### dbt

dbt is a SQL-based transformation framework. Key features:

- **Layered Transformations**: Bronze → Silver → Gold
- **Dependency Management**: Automatic DAG resolution
- **Testing**: Data quality assertions
- **Documentation**: Auto-generated lineage

**Learn more**: [ARCHITECTURE.md - dbt](../ARCHITECTURE.md#4-dbt-transformations)

### Dagster

Dagster is an asset-based orchestration platform. Key features:

- **Software-Defined Assets**: Declarative data pipeline
- **Lineage Tracking**: Automatic dependency graph
- **Partitioning**: Daily/hourly partition support
- **Freshness Policies**: Monitor asset health

**Learn more**: [ARCHITECTURE.md - Dagster](../ARCHITECTURE.md#5-dagster-orchestration)

## Common Workflows

### 1. Daily Ingestion

```bash
# Ingest raw data to dev branch
docker exec dagster-webserver dagster asset materialize --select entries
```

This fetches data from the Nightscout API, stages it to S3, and registers it as an Iceberg table on the `dev` branch.

**Learn more**: [QUICK_START.md - First Pipeline Run](../QUICK_START.md#step-6-run-your-first-pipeline)

### 2. Transformation

```bash
# Run dbt transformations (bronze → silver → gold)
docker exec dagster-webserver dagster asset materialize --select "dbt:*"
```

This executes dbt models to transform raw data into curated analytics tables.

**Learn more**: [ARCHITECTURE.md - Transformation Pipeline](../ARCHITECTURE.md#transformation-pipeline)

### 3. Promotion

```bash
# Merge dev branch to main (production)
docker exec dagster-webserver dagster asset materialize --select promote_dev_to_main
```

This atomically promotes all validated data from dev to main.

**Learn more**: [NESSIE_WORKFLOW.md - Merging Dev to Main](../NESSIE_WORKFLOW.md#merging-dev-to-main)

### 4. Publishing

```bash
# Publish curated marts to Postgres for BI
docker exec dagster-webserver dagster asset materialize --select "postgres_*"
```

This materializes business metrics tables in Postgres for fast dashboard queries.

**Learn more**: [ARCHITECTURE.md - Publishing Pipeline](../ARCHITECTURE.md#publishing-pipeline)

### 5. Ad-hoc Analysis

```python
# Query Iceberg tables with DuckDB
import duckdb

conn = duckdb.connect()
conn.execute("INSTALL iceberg; LOAD iceberg;")

# Configure S3
conn.execute("""
    SET s3_endpoint='localhost:9000';
    SET s3_access_key_id='minioadmin';
    SET s3_secret_access_key='password123';
""")

# Query
df = conn.execute("""
    SELECT * FROM iceberg_scan('s3://lake/warehouse/raw/entries/metadata/v1.metadata.json')
    LIMIT 10;
""").df()

print(df)
```

**Learn more**: [duckdb-iceberg-queries.md](./duckdb-iceberg-queries.md)

## Service URLs

When Cascade is running, access these web interfaces:

| Service | URL | Purpose |
|---------|-----|---------|
| **Hub** | http://localhost:10009 | Service status dashboard |
| **Dagster** | http://localhost:10006 | Orchestration UI |
| **Nessie** | http://localhost:10003/api/v2/config | Catalog API |
| **Trino** | http://localhost:10005 | Query engine UI |
| **MinIO Console** | http://localhost:10002 | Object storage admin |
| **Superset** | http://localhost:10007 | BI dashboards |
| **pgweb** | http://localhost:10008 | PostgreSQL admin |
| **OpenMetadata** | http://localhost:10020 | Data catalog and discovery |
| **FastAPI** | http://localhost:10010 | REST API (docs) |
| **Hasura** | http://localhost:10011 | GraphQL API |
| **Grafana** | http://localhost:10016 | Monitoring dashboards |

**Learn more**: [QUICK_START.md - Verify Services](../QUICK_START.md#step-4-verify-services)

## Configuration

All configuration is managed via environment variables in `.env`:

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Key settings**:
- `NESSIE_PORT`, `NESSIE_VERSION` - Nessie catalog
- `TRINO_PORT`, `TRINO_VERSION` - Trino query engine
- `ICEBERG_WAREHOUSE_PATH` - Iceberg table storage
- `POSTGRES_*` - Database credentials
- `MINIO_*` - Object storage credentials

**Learn more**: [README.md - Configuration](../README.md#configuration)

## Troubleshooting

### Services Won't Start

```bash
# Check service health
docker compose ps

# View logs
docker compose logs <service-name>

# Restart service
docker compose restart <service-name>
```

**Learn more**: [QUICK_START.md - Troubleshooting](../QUICK_START.md#troubleshooting)

### Asset Failures

```bash
# View asset details
open http://localhost:3000

# Check logs
docker logs dagster-daemon

# Verify configuration
docker exec dagster-webserver python -c "from cascade.config import config; print(config.model_dump_json(indent=2))"
```

**Learn more**: [QUICK_START.md - Dagster Assets Failing](../QUICK_START.md#dagster-assets-failing)

### Catalog Issues

```bash
# Test Nessie API
curl http://localhost:19120/api/v2/config

# Test Trino connection
docker exec trino trino --execute "SHOW CATALOGS;"

# Verify PyIceberg
docker exec dagster-webserver python -c "from cascade.iceberg.catalog import get_catalog; print(get_catalog().list_namespaces())"
```

**Learn more**: [QUICK_START.md - Catalog Connection Issues](../QUICK_START.md#catalog-connection-issues)

### Fresh Start

```bash
# WARNING: Destroys all data
make clean-all
make fresh-start
```

**Learn more**: [QUICK_START.md - Fresh Start](../QUICK_START.md#fresh-start-nuclear-option)

## Development

### Local Setup

```bash
# Install dependencies
cd services/dagster
uv pip install -e .

# Run type checking
basedpyright src/cascade/

# Run linting
ruff check src/cascade/
ruff format src/cascade/
```

**Learn more**: [README.md - Development](../README.md#development)

### Adding Assets

1. Create asset function in `src/cascade/defs/`
2. Import in `__init__.py`
3. Asset auto-discovered by Dagster

**Learn more**: [README.md - Adding New Assets](../README.md#adding-new-assets)

### Testing

```bash
# Run all tests
pytest tests/

# Run phase-specific tests
./tests/test_phase3_ingestion.sh
./tests/test_phase4_transformation.sh
```

**Learn more**: [README.md - Testing](../README.md#testing)

## Architecture Diagrams

### Data Flow

```
Nightscout API
  ↓
DLT (Python ingestion)
  ↓
S3 Staging (Parquet files)
  ↓
PyIceberg (register/append)
  ↓
Iceberg Tables (on Nessie catalog)
  ↓
Trino (query engine)
  ↓
dbt (transformations: bronze → silver → gold)
  ↓
PostgreSQL Marts (business metrics)
  ↓
Superset (dashboards)
```

**Learn more**: [ARCHITECTURE.md - Data Flow](../ARCHITECTURE.md#data-flow)

### Service Dependencies

```
Nessie → PostgreSQL (metadata storage)
Trino → Nessie (catalog queries)
Trino → MinIO (table data)
Dagster → Trino (orchestration)
Dagster → Nessie (branch management)
Superset → PostgreSQL (marts)
Superset → Trino (Iceberg queries)
```

**Learn more**: [ARCHITECTURE.md - Service Dependencies](../ARCHITECTURE.md#service-dependencies)

## Resources

### Documentation

- [Apache Iceberg](https://iceberg.apache.org/docs/latest/)
- [Project Nessie](https://projectnessie.org/docs/)
- [Trino](https://trino.io/docs/current/)
- [dbt](https://docs.getdbt.com/)
- [Dagster](https://docs.dagster.io/)
- [DuckDB](https://duckdb.org/docs/)

### External Links

- [Iceberg Spec](https://iceberg.apache.org/spec/)
- [Nessie REST API](https://projectnessie.org/develop/rest/)
- [Trino Iceberg Connector](https://trino.io/docs/current/connector/iceberg.html)
- [dbt-trino Adapter](https://github.com/starburstdata/dbt-trino)
- [PyIceberg](https://py.iceberg.apache.org/)

## Contributing

Cascade is a personal project demonstrating modern data lakehouse patterns. Feel free to:

- Fork and adapt for your needs
- Open issues for bugs or questions
- Submit pull requests for improvements

## License

MIT License - See LICENSE file for details.

## Support

For questions or issues:

1. Check the troubleshooting sections in relevant guides
2. Review [ARCHITECTURE.md](../ARCHITECTURE.md) for technical details
3. Open an issue on GitHub

---

**Quick Links**:
- [Quick Start](../QUICK_START.md)
- [Architecture](../ARCHITECTURE.md)
- [Nessie Workflow](../NESSIE_WORKFLOW.md)
- [DuckDB Queries](./duckdb-iceberg-queries.md)
