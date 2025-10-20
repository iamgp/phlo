# Quick Start Guide

This guide will get you up and running with Cascade in under 10 minutes.

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
  - Minimum 8GB RAM allocated to Docker
  - 20GB free disk space
- **`uv`** (for Python development): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git** (to clone the repository)

## Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-username/cascade.git
cd cascade

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set passwords for security:
# - POSTGRES_PASSWORD
# - MINIO_ROOT_PASSWORD
nano .env  # or use your preferred editor
```

## Step 2: Start Services

Cascade uses Docker Compose profiles to start services in groups.

### Start All Services (Recommended for First Run)

```bash
make up-all
```

This starts:
- **Core**: PostgreSQL, MinIO, Dagster, Hub
- **Query**: Trino, Nessie
- **BI**: Superset, pgweb
- **Documentation**: MkDocs

### Alternative: Start Service Groups Individually

```bash
# Core services (required)
make up-core

# Query services (Trino + Nessie)
make up-query

# BI services (optional)
make up-bi

# Documentation (optional)
docker compose --profile docs up -d mkdocs
```

## Step 3: Access Services

Wait about 30 seconds for all services to start, then access:

- **Hub**: http://localhost:10009 - Service status dashboard
- **Dagster**: http://localhost:10006 - Orchestration UI
- **Documentation**: http://localhost:10012 - MkDocs documentation
- **Nessie**: http://localhost:10003/api/v2/config - Catalog API
- **Trino**: http://localhost:10005 - Query engine (UI)
- **MinIO Console**: http://localhost:10002 - Object storage
- **Superset**: http://localhost:10007 - Dashboards (admin/admin)

## Step 4: Run Your First Pipeline

```bash
# Materialize the Nightscout entries asset
docker exec dagster-webserver dagster asset materialize --select entries
```

Check the Dagster UI to see the pipeline run and explore the data.

## Next Steps

- Read the full [Quick Start Guide](../../QUICK_START.md) for detailed instructions
- Learn about the [Architecture](architecture.md)
- Configure your environment in the [Configuration Guide](configuration.md)
- Explore the [API documentation](api.md)
