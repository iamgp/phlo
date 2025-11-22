# Cascade

A production-ready data lakehouse platform built on Apache Iceberg and Project Nessie, providing Git-like version control for data with ACID transactions and time travel capabilities.

## Features

- **Git-like data workflows** with branching, merging, and atomic commits via Project Nessie
- **Time travel queries** to access data at any historical point
- **ACID transactions** with schema evolution using Apache Iceberg
- **Multi-engine analytics** supporting Trino, DuckDB, and future Spark integration
- **Complete observability** with Grafana, Prometheus, and Loki
- **REST and GraphQL APIs** for programmatic data access
- **Asset-based orchestration** using Dagster with full lineage tracking

## Quick Start

### Prerequisites

- Docker and Docker Compose
- `uv` (for local development)

### Setup

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services:**
   ```bash
   make up-all
   ```

   Or start specific service groups:
   ```bash
   make up-core          # Core data platform
   make up-query         # Query engines
   make up-bi            # Business intelligence
   make up-api           # REST & GraphQL APIs
   make up-observability # Monitoring stack
   ```

3. **Access the platform:**
   ```bash
   make hub       # Service dashboard (localhost:10009)
   make dagster   # Orchestration (localhost:10006)
   make superset  # BI dashboards (localhost:10007)
   ```

### Run Your First Pipeline

```bash
# Ingest data
docker exec dagster-webserver dagster asset materialize --select entries

# Transform with dbt
docker exec dagster-webserver dagster asset materialize --select "dbt:*"

# Publish to marts
docker exec dagster-webserver dagster asset materialize --select "postgres_*"
```

## Core Components

- **[Apache Iceberg](https://iceberg.apache.org/)** - Open table format with ACID and time travel
- **[Project Nessie](https://projectnessie.org/)** - Git-like catalog with branching
- **[Trino](https://trino.io/)** - Distributed SQL query engine
- **[dbt](https://www.getdbt.com/)** - SQL transformations and modeling
- **[Dagster](https://dagster.io/)** - Asset-based orchestration
- **[MinIO](https://min.io/)** - S3-compatible object storage
- **[Superset](https://superset.apache.org/)** - Business intelligence
- **[FastAPI](https://fastapi.tiangolo.com/)** & **[Hasura](https://hasura.io/)** - REST and GraphQL APIs
- **[Grafana Stack](https://grafana.com/)** - Observability (Prometheus, Loki, Alloy)

## Documentation

- **[Architecture Guide](./docs/ARCHITECTURE.md)** - System design and component details
- **[Quick Start Guide](./docs/QUICK_START.md)** - Detailed setup instructions
- **[Nessie Workflow](./docs/NESSIE_WORKFLOW.md)** - Data branching and promotion patterns
- **[DuckDB Analysis](./docs/duckdb-iceberg-queries.md)** - Ad-hoc query examples

## Development

### Local Setup

```bash
make setup                    # Install dependencies
basedpyright src/cascade/     # Type checking
ruff check src/cascade/       # Linting
pytest tests/                 # Run tests
```

### Configuration

All services configured via `.env` file. See `src/cascade/config.py` for schema.

### Project Structure

```
cascade/
├── src/cascade/          # Dagster assets and core logic
│   ├── defs/            # Ingestion, transformation, publishing assets
│   ├── iceberg/         # PyIceberg catalog and tables
│   └── schemas/         # Data validation schemas
├── transforms/dbt/      # dbt models (bronze/silver/gold/marts)
├── services/            # API services (FastAPI, Hub dashboard)
├── docker/              # Service configurations
└── docs/                # Documentation
```

## Example Use Case

Includes a complete Nightscout CGM data pipeline demonstrating:
- API ingestion → Iceberg tables
- Multi-layer transformations (bronze/silver/gold)
- PostgreSQL marts for BI
- Superset dashboards

Perfect for learning modern data engineering patterns.

## Production Deployment

- **Docker Compose** for development and small deployments
- **Kubernetes** ready (Helm charts planned)
- **Cloud storage** compatible (S3, GCS, Azure Blob)
- **12-factor compliant** with stateless services

See [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for production hardening.

## Contributing

This is a personal project demonstrating modern data lakehouse patterns. Feel free to fork and adapt.

## License

MIT License - See LICENSE file for details.
