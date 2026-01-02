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
uv pip install phlo[defaults]

# Initialize a new project
phlo init my-project
cd my-project

# Initialize infrastructure (generates .phlo/.env and .phlo/.env.local)
phlo services init

# Start services
phlo services start
```

## Detailed Installation Steps

### Step 1: Install Phlo

Install Phlo and its default services:

```bash
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
├── .env.example         # Local secrets template (.phlo/.env.local)
├── workflows/           # Data ingestion workflows
│   ├── ingestion/
│   ├── schemas/
│   └── transforms/      # dbt transformations
│       └── dbt/
├── tests/               # Test files
└── phlo.yaml           # Project configuration
```

### Step 3: Configure Environment

Configure non-secret defaults in `phlo.yaml` and secrets in `.phlo/.env.local`:

```bash
phlo services init
```

Edit `phlo.yaml` (env:) and `.phlo/.env.local` with your settings. The defaults work for local development:

```bash
# phlo.yaml (committed)
env:
  POSTGRES_PORT: 10000
  MINIO_API_PORT: 10001
  MINIO_CONSOLE_PORT: 10002
  NESSIE_PORT: 10003
  TRINO_PORT: 10005
  DAGSTER_PORT: 10006

# .phlo/.env.local (not committed)
POSTGRES_PASSWORD=phlo
MINIO_ROOT_PASSWORD=minio123
SUPERSET_ADMIN_PASSWORD=admin
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

**First-time setup**: `phlo services start` will initialize `.phlo/` if it doesn't exist, but run `phlo services init` first if you want to edit `phlo.yaml` and `.phlo/.env.local` before startup.

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
uv pip install phlo
```

Then install services individually as needed:

```bash
uv pip install phlo-dagster phlo-postgres phlo-trino
```

### With Optional Services

Install additional service packages:

```bash
# Business intelligence
uv pip install phlo-superset

# Observability stack
uv pip install phlo-prometheus phlo-grafana phlo-loki phlo-alloy

# API layers
uv pip install phlo-postgrest phlo-hasura

# Data catalog
uv pip install phlo-openmetadata
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

If ports are already in use, edit `phlo.yaml` (env:) to change port numbers:

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
