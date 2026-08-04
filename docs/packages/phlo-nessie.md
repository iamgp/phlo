# phlo-nessie

Nessie Git-like catalog for Phlo.

## Overview

`phlo-nessie` provides Git-like version control for Iceberg tables. It enables branching, merging, and time travel for the data lakehouse, allowing teams to work on data in isolation before merging to production.

## Installation

```bash
pip install phlo-nessie
# or
phlo plugin install nessie

# Nessie plus the Trino catalog adapter
pip install 'phlo-nessie[trino]'
```

## Configuration

| Variable               | Default   | Description                |
| ---------------------- | --------- | -------------------------- |
| `NESSIE_PORT`          | `10003`   | Nessie API host port       |
| `NESSIE_VERSION`       | `0.107.2` | Nessie version             |
| `NESSIE_OIDC_ENABLED`  | `false`   | Enable OIDC authentication |
| `NESSIE_AUTHZ_ENABLED` | `false`   | Enable authorization       |

## Features

### Apache Iceberg 1.11 Compatibility

`phlo-nessie` validates the Trino REST catalog properties that connect Trino to
Nessie's Iceberg REST surface for Apache Iceberg 1.11 compatibility:

| Check | Expectation |
| --- | --- |
| Connector | `connector.name=iceberg`. |
| Catalog type | `iceberg.catalog.type=rest`. |
| REST endpoint | `iceberg.rest-catalog.uri` points at `/iceberg`. |
| Ref routing | Branch-specific Trino catalogs use `iceberg.rest-catalog.prefix`. |
| Warehouse | `iceberg.rest-catalog.warehouse` is configured. |
| S3 compatibility | Native S3 and path-style access are enabled. |

### Auto-Configuration

| Feature              | How It Works                                               |
| -------------------- | ---------------------------------------------------------- |
| **Branch Init**      | Auto-creates `main` and `dev` branches via post_start hook |
| **Metrics Labels**   | Exposes Quarkus metrics at `/q/metrics`                    |
| **Postgres Storage** | Uses PostgreSQL for version store (default backend)        |
| **Catalog Backend**  | Exposes Nessie Iceberg REST endpoints for optional engine adapters |
| **Trino Adapter**    | `phlo-nessie[trino]` registers `iceberg` and `iceberg_dev` catalogs |

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
phlo branch list

# Create a new branch
phlo branch create feature/my-feature --from main

# Delete a branch
phlo branch delete feature/my-feature

# Merge branches
phlo branch merge dev main
```

### Write-Audit-Publish Pattern

Phlo uses Nessie branches for the Write-Audit-Publish (WAP) pattern:

```
1. Write Phase
   └── Data lands on isolated branch: pipeline-run-{logical_run_id}

2. Audit Phase
   └── Quality checks validate data on the branch

3. Publish Phase
   └── Auto-promotion sensor merges to main when checks pass
```

### Branch Lifecycle

```python
# Create feature branch
from phlo_nessie import NessieResource

nessie = NessieResource()
nessie.create_branch("feature/new-data", from_ref="main")

# Work on the branch...

# Merge when ready
nessie.merge_branch("feature/new-data", target="main")

# Clean up
nessie.delete_branch("feature/new-data")
```

## Branching Strategy

| Branch Pattern      | Purpose                              |
| ------------------- | ------------------------------------ |
| `main`              | Production data (read-only for most) |
| `dev`               | Development workspace                |
| `pipeline-run-{id}` | Isolated pipeline execution          |
| `feature/*`         | Feature development                  |

## Endpoints

| Endpoint         | URL                                |
| ---------------- | ---------------------------------- |
| **API v1**       | `http://localhost:10003/api/v1`    |
| **API v2**       | `http://localhost:10003/api/v2`    |
| **Iceberg REST** | `http://localhost:10003/iceberg`   |
| **Metrics**      | `http://localhost:10003/q/metrics` |

## API Examples

```bash
# Get server config
curl http://localhost:10003/api/v2/config

# List branches
curl http://localhost:10003/api/v2/trees

# Get branch details
curl http://localhost:10003/api/v2/trees/main
```

## Entry Points

| Entry Point                     | Plugin                                          |
| ------------------------------- | ----------------------------------------------- |
| `phlo.plugins.services`         | `NessieServicePlugin`                           |
| `phlo.plugins.cli`              | Branch management CLI (`branch` group)         |
| `phlo.plugins.catalogs`         | Nessie catalog adapters (optional Trino adapter in `phlo-nessie[trino]`) |
| `phlo.plugins.resource_providers` | `NessieResourceProvider`                       |
## Related Packages

- [phlo-iceberg](phlo-iceberg.md) - Iceberg table format
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-postgres](phlo-postgres.md) - Backend storage

## Next Steps

- [Core Concepts](../getting-started/core-concepts.md) - Understand WAP pattern
- [Architecture Reference](../reference/architecture.md) - System design
- [Workflow Development](../guides/workflow-development.md) - Build pipelines
