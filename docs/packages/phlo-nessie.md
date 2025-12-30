# phlo-nessie

Nessie Git-like catalog for Phlo.

## Overview

`phlo-nessie` provides Git-like version control for Iceberg tables. It enables branching, merging, and time travel for the data lakehouse, allowing teams to work on data in isolation before merging to production.

## Installation

```bash
pip install phlo-nessie
# or
phlo plugin install nessie
```

## Configuration

| Variable               | Default   | Description                |
| ---------------------- | --------- | -------------------------- |
| `NESSIE_PORT`          | `19120`   | Nessie API port            |
| `NESSIE_VERSION`       | `0.106.0` | Nessie version             |
| `NESSIE_OIDC_ENABLED`  | `false`   | Enable OIDC authentication |
| `NESSIE_AUTHZ_ENABLED` | `false`   | Enable authorization       |

## Features

### Auto-Configuration

| Feature              | How It Works                                               |
| -------------------- | ---------------------------------------------------------- |
| **Branch Init**      | Auto-creates `main` and `dev` branches via post_start hook |
| **Metrics Labels**   | Exposes Quarkus metrics at `/q/metrics`                    |
| **Postgres Storage** | Uses PostgreSQL for version store (default backend)        |

### Post-Start Hook

```yaml
hooks:
  post_start:
    - name: init-branches
      command: python -m phlo_nessie.hooks init-branches
```

## Usage

### CLI Commands

```bash
# Start Nessie
phlo services start --service nessie

# List branches
phlo nessie branches

# Create a new branch
phlo nessie branch create feature/my-feature

# Delete a branch
phlo nessie branch delete feature/my-feature

# Merge branches
phlo nessie merge dev main
```

### Write-Audit-Publish Pattern

Phlo uses Nessie branches for the Write-Audit-Publish (WAP) pattern:

```
1. Write Phase
   └── Data lands on isolated branch: pipeline/run-{run_id}

2. Audit Phase
   └── Quality checks validate data on the branch

3. Publish Phase
   └── Auto-promotion sensor merges to main when checks pass
```

### Branch Lifecycle

```python
# Create feature branch
from phlo_nessie.client import NessieClient

client = NessieClient()
client.create_branch("feature/new-data", from_ref="main")

# Work on the branch...

# Merge when ready
client.merge("feature/new-data", "main")

# Clean up
client.delete_branch("feature/new-data")
```

## Branching Strategy

| Branch Pattern      | Purpose                              |
| ------------------- | ------------------------------------ |
| `main`              | Production data (read-only for most) |
| `dev`               | Development workspace                |
| `pipeline/run-{id}` | Isolated pipeline execution          |
| `feature/*`         | Feature development                  |

## Endpoints

| Endpoint         | URL                                |
| ---------------- | ---------------------------------- |
| **API v1**       | `http://localhost:19120/api/v1`    |
| **API v2**       | `http://localhost:19120/api/v2`    |
| **Iceberg REST** | `http://localhost:19120/iceberg`   |
| **Metrics**      | `http://localhost:19120/q/metrics` |

## API Examples

```bash
# Get server config
curl http://localhost:19120/api/v2/config

# List branches
curl http://localhost:19120/api/v2/trees

# Get branch details
curl http://localhost:19120/api/v2/trees/main
```

## Entry Points

| Entry Point             | Plugin                |
| ----------------------- | --------------------- |
| `phlo.plugins.services` | `NessieServicePlugin` |
| `phlo.plugins.cli`      | Nessie CLI commands   |

## Related Packages

- [phlo-iceberg](phlo-iceberg.md) - Iceberg table format
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-postgres](phlo-postgres.md) - Backend storage

## Next Steps

- [Core Concepts](../getting-started/core-concepts.md) - Understand WAP pattern
- [Architecture Reference](../reference/architecture.md) - System design
- [Workflow Development](../guides/workflow-development.md) - Build pipelines
