# Installation Guide

Complete guide to installing and setting up Phlo on your system.

## Prerequisites

### Required

- **Python**: 3.11 or later
- **Docker**: Version 20.10 or later (for running infrastructure services)
- **Docker Compose**: Version 2.0 or later

### Recommended

- **uv**: Fast Python package installer (recommended for better performance)
- **8GB RAM**: Minimum for running all services
- **20GB disk space**: For Docker volumes and data

## Quick Install

```bash
# Install Phlo with default services
pip install phlo[defaults]

# Or using uv (recommended)
uv pip install phlo[defaults]

# Initialize a new project
phlo init my-project
cd my-project

# Copy environment template
cp .env.example .env

# Start services
phlo services start
```

## Detailed Installation Steps

### Step 1: Install Phlo

Install Phlo and its default services:

```bash
# Using pip
pip install phlo[defaults]

# Using uv (recommended for faster installs)
uv pip install phlo[defaults]
```

The `[defaults]` extra installs these core service packages:
- `phlo-dagster` - Data orchestration platform
- `phlo-postgres` - PostgreSQL database
- `phlo-trino` - Distributed SQL query engine
- `phlo-nessie` - Git-like catalog for Iceberg
- `phlo-minio` - S3-compatible object storage

Verify installation:

```bash
phlo --version
```

### Step 2: Initialize a Project

Create a new Phlo project:

```bash
phlo init my-project
cd my-project
```

This creates:
```
my-project/
├── .env.example         # Environment variables template
├── workflows/           # Data ingestion workflows
│   ├── ingestion/
│   └── schemas/
├── transforms/          # dbt transformations
│   └── dbt/
├── tests/               # Test files
└── phlo.yaml           # Project configuration
```

### Step 3: Configure Environment

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

### Step 4: Start Services

Start the infrastructure services:

```bash
phlo services start
```

This automatically:
1. Initializes the `.phlo/` directory with Docker configurations
2. Starts all service containers:
   - PostgreSQL (port 10000)
   - MinIO (ports 10001-10002)
   - Nessie (port 10003)
   - Trino (port 10005)
   - Dagster webserver (port 10006)
   - Dagster daemon

**First-time setup**: The first `phlo services start` automatically runs initialization, so you don't need a separate `phlo services init` command.

### Step 5: Verify Installation

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

### Step 6: Create and Run Your First Pipeline

Create a workflow using the interactive wizard:

```bash
phlo create-workflow
```

Or materialize the example assets (if using a template with examples):

```bash
phlo materialize --all
```

You can also use the Dagster UI at http://localhost:10006 to materialize assets.

## Installation Options

### Minimal Installation

Install only the core Phlo framework without service packages:

```bash
pip install phlo
```

Then install services individually as needed:

```bash
pip install phlo-dagster phlo-postgres phlo-trino
```

### With Optional Services

Install additional service packages:

```bash
# Business intelligence
pip install phlo-superset

# Observability stack
pip install phlo-prometheus phlo-grafana phlo-loki phlo-alloy

# API layers
pip install phlo-postgrest phlo-hasura

# Data catalog
pip install phlo-openmetadata
```

Start with service profiles:

```bash
# With observability (Prometheus, Grafana, Loki)
phlo services start --profile observability

# With API layer (PostgREST, Hasura)
phlo services start --profile api

# With data catalog
phlo services start --profile catalog

# Multiple profiles
phlo services start --profile observability --profile api
```

### Native Services Mode

Run Observatory and phlo-api as native Python processes instead of Docker containers (useful on ARM Macs or for development):

```bash
phlo services start --native
```

This runs:
- All infrastructure services (Postgres, Trino, etc.) in Docker
- Observatory UI and phlo-api as Python subprocesses
- Better performance on non-Linux systems

### Development Mode

For developing Phlo itself, mount local source code:

```bash
phlo services init --dev --phlo-source /path/to/phlo
phlo services start
```

This mounts the phlo monorepo into the Dagster container and installs `phlo[defaults]` as an editable install, allowing you to modify Phlo's source code and see changes immediately.

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
