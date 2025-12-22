# Installation Guide

Complete guide to installing and setting up Phlo on your system.

## Prerequisites

### Required
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Python**: 3.11 or later (for CLI usage)
- **Git**: For cloning the repository

### Recommended
- **uv**: Fast Python package installer (optional, but recommended)
- **Make**: For using convenience commands
- **8GB RAM**: Minimum for running all services
- **20GB disk space**: For Docker volumes and data

## Quick Install

```bash
# Clone repository
git clone https://github.com/iamgp/phlo.git
cd phlo

# Copy environment template
cp .env.example .env

# Start services
phlo services start
```

## Detailed Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/iamgp/phlo.git
cd phlo
```

### Step 2: Configure Environment

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Edit `.env` with your settings. The defaults work for local development:

```bash
# Database
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=10000

# Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_HOST=minio
MINIO_PORT=10001

# Catalog
NESSIE_HOST=nessie
NESSIE_PORT=10003

# Query Engine
TRINO_HOST=trino
TRINO_PORT=10005

# Iceberg
ICEBERG_WAREHOUSE_PATH=s3://lake/warehouse
ICEBERG_STAGING_PATH=s3://lake/stage

# Branch Management
BRANCH_RETENTION_DAYS=7
AUTO_PROMOTE_ENABLED=true
BRANCH_CLEANUP_ENABLED=false
```

### Step 3: Install Phlo CLI (Optional)

The CLI provides convenient commands for managing services and workflows:

```bash
# Using pip
pip install -e .

# Using uv (recommended)
uv pip install -e .
```

Verify installation:

```bash
phlo --version
```

Install the core service packages (recommended):

```bash
uv pip install -e ".[core-services]"
```

These packages provide the Docker service definitions used by `phlo services`.

### Step 4: Initialize Infrastructure

Create the infrastructure directory structure:

```bash
phlo services init
```

This creates `.phlo/` directory with Docker configurations.

### Step 5: Start Services

Start the core services:

```bash
phlo services start
```

This starts:
- PostgreSQL (port 10000)
- MinIO (ports 10001-10002)
- Nessie (port 10003)
- Trino (port 10005)
- Dagster webserver (port 10006)
- Dagster daemon

### Step 6: Verify Installation

Check service status:

```bash
phlo services status
```

Expected output:
```
SERVICE              STATUS    PORTS
postgres             running   10000
minio                running   10001-10002
nessie               running   10003
trino                running   10005
dagster-webserver    running   10006
dagster-daemon       running
```

Access Dagster UI:
```bash
# Open in browser
open http://localhost:10006
```

### Step 7: Run Example Pipeline

Materialize the example glucose data:

```bash
phlo materialize dlt_glucose_entries
```

Or use the Dagster UI to materialize assets.

## Installation Options

### Development Mode

Mount local source code for development:

```bash
phlo services start --dev
```

This rebuilds containers using `Dockerfile.dev` with local source mounted.

### With Optional Services

Start with additional profiles:

```bash
# With observability (Prometheus, Grafana, Loki)
phlo services start --profile observability

# With API layer (PostgREST, Hasura)
phlo services start --profile api

# With both
phlo services start --profile observability --profile api
```

### Production Deployment

For production deployments, see the [Production Deployment Guide](../operations/production-deployment.md).

## Verify Components

### PostgreSQL
```bash
docker exec -it phlo-postgres-1 psql -U postgres
```

### MinIO
Open http://localhost:10001 in browser
- Username: minioadmin
- Password: minioadmin

### Nessie
```bash
curl http://localhost:10003/api/v2/config
```

### Trino
```bash
docker exec -it phlo-trino-1 trino
```

## Troubleshooting

### Services won't start

Check Docker is running:
```bash
docker ps
```

View logs:
```bash
phlo services logs -f
```

### Port conflicts

If ports are already in use, edit `.env` to change port numbers:
```bash
POSTGRES_PORT=15432
MINIO_PORT=19000
# etc.
```

### Insufficient resources

Ensure Docker has enough resources:
- **Docker Desktop**: Settings → Resources → 8GB RAM minimum
- **Linux**: Check `docker info` for resource limits

### Permission errors

On Linux, you may need to fix permissions:
```bash
sudo chown -R $USER:$USER .phlo/
```

## Uninstall

Stop and remove all services:

```bash
# Stop services
phlo services stop

# Remove volumes (deletes all data)
phlo services stop --volumes
```

Remove Phlo directory:
```bash
cd ..
rm -rf phlo
```

## Next Steps

- [Quickstart Guide](quickstart.md) - Run your first pipeline
- [CLI Reference](../reference/cli-reference.md) - Learn CLI commands
- [Configuration Reference](../reference/configuration-reference.md) - Advanced configuration
- [Troubleshooting](../operations/troubleshooting.md) - Common issues
