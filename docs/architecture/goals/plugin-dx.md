# Plugin System DX Goals

> **Vision**: A user should be able to compose their perfect data lakehouse by installing Python packages, with zero infrastructure configuration for common use cases and simple overrides for advanced cases.

## Architecture: Core vs Packages

Phlo has a clear separation between **core** (bundled, non-swappable) and **packages** (installable, swappable):

```
┌─────────────────────────────────────────────────────────────┐
│                     PHLO CORE (Glue)                        │
│  - CLI (phlo services, phlo materialize, etc.)              │
│  - Decorators (@phlo.ingestion, @phlo.quality)              │
│  - Config system (phlo.yaml parsing)                        │
│  - Plugin registry & discovery                              │
│  - Service composer (docker-compose generation)             │
└─────────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  OBSERVATORY  │  │  phlo-api    │  │  PACKAGES (plugins)  │
│  (Core App)   │  │  (Core API)  │  │                      │
│               │  │              │  │  phlo-dagster  ──┐   │
│  THE phlo UI  │  │  Exposes     │  │  phlo-airflow ──┴─ swap
│  Bundled      │  │  internals   │  │                      │
│               │  │  to Obs.     │  │  phlo-postgres ─┐    │
└───────────────┘  └──────────────┘  │  phlo-mysql ────┴─ swap
                                     │                      │
                                     │  phlo-trino ────┐    │
                                     │  phlo-duckdb ───┴─ swap
                                     │                      │
                                     │  phlo-minio         │
                                     │  phlo-nessie        │
                                     │  phlo-superset      │
                                     │  phlo-grafana       │
                                     │  etc.               │
                                     └──────────────────────┘
```

### What's Core (Bundled with `pip install phlo`)

| Component        | Purpose                                                 |
| ---------------- | ------------------------------------------------------- |
| **phlo library** | CLI, decorators, config, plugin system                  |
| **Observatory**  | THE phlo UI — lineage, data explorer, quality dashboard |
| **phlo-api**     | Python backend exposing phlo internals to Observatory   |

Observatory is unique:

- It's literally "the face of phlo"
- There's no alternative (unlike Dagster vs Airflow)
- It should evolve with phlo core
- Every phlo user gets it

### What's a Package (Swappable)

Everything that's a **commodity** or has **alternatives**:

| Package       | Category      | Alternatives                     |
| ------------- | ------------- | -------------------------------- |
| phlo-dagster  | Orchestrator  | phlo-airflow, phlo-prefect       |
| phlo-postgres | Database      | phlo-mysql                       |
| phlo-trino    | Query Engine  | phlo-duckdb                      |
| phlo-nessie   | Catalog       | (future: other Iceberg catalogs) |
| phlo-minio    | Storage       | phlo-s3 (direct AWS)             |
| phlo-superset | BI            | phlo-metabase                    |
| phlo-grafana  | Observability | -                                |
| phlo-loki     | Logs          | -                                |

---

## The Goal: Best-in-Class DX

### 1. Zero-Config by Default

**User Story**: _"I installed phlo with defaults and it just worked."_

```bash
# Option A: Explicit package selection
pip install phlo phlo-dagster phlo-postgres phlo-trino phlo-nessie phlo-minio
cd my-project
phlo init .
phlo services start

# Option B: Install with curated defaults
pip install phlo[defaults]  # Includes dagster, postgres, trino, nessie, minio
phlo init .
phlo services start

# Either way, Observatory is at :3001 automatically (it's core)
```

The plugin system should:

- **Auto-discover** installed packages via entry points
- **Auto-configure** connections between services (Observatory connects to Trino, Grafana scrapes Prometheus, etc.)
- **Start with sensible defaults** that work for 80% of users
- **Require zero `phlo.yaml` configuration** for basic usage

### 2. Declarative Composition

**User Story**: _"I want to swap Superset for Metabase, and override Observatory's port."_

```yaml
# phlo.yaml - only write what you want to change
name: my-lakehouse

services:
  # Disable an installed package service
  superset:
    enabled: false

  # Override settings for core Observatory
  observatory:
    port: 8080
    environment:
      CUSTOM_FEATURE: "enabled"

  # Add a custom service not from a package
  custom-api:
    type: inline
    image: my-registry/custom-api:latest
    ports:
      - "4000:4000"
    depends_on:
      - trino
```

### 3. The "Pre-Connected" Promise

**User Story**: _"Services talk to each other without me configuring endpoints."_

When you install packages, they should auto-wire:

- Observatory → Dagster (for assets/lineage)
- Observatory → Trino (for queries)
- Observatory → Nessie (for branches)
- Grafana → Prometheus (for metrics)

This is achieved through:

1. **Standard environment variable conventions** (TRINO_URL, NESSIE_URL, etc.)
2. **Compose generation** that wires services together
3. **phlo-api** backend that exposes phlo internals to Observatory

### 4. First-Class Local Development

**User Story**: _"I'm developing a custom service and want it to hot-reload."_

```bash
# Dev mode mounts source for live changes
phlo services init --dev --phlo-source /path/to/phlo
phlo services start

# My custom service code changes are immediately reflected
```

### 5. Simple Extension

**User Story**: _"I want to create a custom service package for my team."_

```bash
phlo plugin create my-cache --type service
# Creates boilerplate with:
# - service.yaml (service definition)
# - Dockerfile
# - README.md
# - pyproject.toml with entry points
```

Then install it:

```bash
cd my-cache && pip install -e .
phlo services start  # my-cache is now available
```

---

## Current State Analysis

### What Works Today

1. **Entry point discovery** - Packages register via `phlo.plugins.services` entry points
2. **Service plugin structure** - Each package has a `service.yaml` bundled and a `plugin.py`
3. **Compose generation** - `phlo services init` generates docker-compose from discovered services
4. **Dev mode** - `--dev` flag applies overrides from `service.yaml`'s `dev` section
5. **Profile grouping** - Services can be grouped into profiles (e.g., `observability`)

### What's Missing

| Gap                               | Impact                                          | Proposed Solution                                 |
| --------------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| **Observatory as plugin**         | Awkward DX, can't control phlo                  | Move to core, add phlo-api backend                |
| **No user overrides**             | Users can't customize installed service configs | Allow `services:` overrides in `phlo.yaml`        |
| **No enable/disable**             | Can't easily disable installed services         | Add `enabled: true/false` per service             |
| **Limited env var configuration** | Only `.env` file, no per-service env in yaml    | Support `environment:` in service overrides       |
| **No port overrides**             | Must edit bundled service.yaml or use env vars  | Support `ports:` in service overrides             |
| **No custom inline services**     | Can't easily add non-packaged services          | Support inline service definitions in `phlo.yaml` |

---

## Proposed DX Model

### Tier 1: Zero-Config (Most Users)

```bash
pip install phlo[defaults]
phlo init my-lakehouse
cd my-lakehouse
phlo services start
# → All default services running
# → Observatory at :3001 (core, always there)
```

The generated `phlo.yaml` is minimal:

```yaml
name: my-lakehouse
```

### Tier 2: Simple Overrides (Power Users)

```yaml
# phlo.yaml
name: my-lakehouse

services:
  observatory:
    port: 8080
    environment:
      DEBUG: "true"

  superset:
    enabled: false # Don't want BI layer
```

This merges with the package's `service.yaml` at compose generation time.

### Tier 3: Custom Services (Advanced Users)

```yaml
# phlo.yaml
name: my-lakehouse

services:
  # Override core Observatory
  observatory:
    port: 8080

  # Define a custom service inline
  custom-api:
    type: inline
    image: my-registry/api:latest
    ports:
      - "4000:4000"
    environment:
      TRINO_URL: http://trino:8080
    depends_on:
      - trino
```

### Tier 4: Create & Publish Packages (Contributors)

```bash
# Create package scaffolding
phlo plugin create my-service --type service

# Develop locally
cd my-service
pip install -e .
phlo services start  # Service is discovered and running

# Publish for others
# 1. Push to PyPI
# 2. Optionally register with phlo registry for `phlo plugin install my-service`
```

---

## Implementation Principles

### 1. Configuration Layering

```
Base Layer:        Package's service.yaml (bundled in pip package)
     ↓
User Override:     phlo.yaml services section
     ↓
Environment:       .env file and process environment
     ↓
Runtime:           CLI flags (--dev, --profile, etc.)
```

Each layer can override values from the previous layer.

### 2. Explicit is Better Than Implicit

- A service is started because it's `default: true` OR explicitly listed
- Users can see exactly what's happening with `phlo services list`
- Overrides are visible in `phlo.yaml`, not hidden in env vars

### 3. Convention Over Configuration

- Standard environment variables: `TRINO_URL`, `NESSIE_URL`, `DAGSTER_URL`, etc.
- Standard ports: Each service has a well-known default port
- Standard container naming: `{project}-{service}-1`

### 4. Fail Fast and Clear

- Validate phlo.yaml against a schema before starting services
- Clear error messages when services fail to start
- `phlo services status` shows exactly what's running/failed

---

## Comparison with Best-in-Class Tools

### Docker Compose DX

```yaml
# docker-compose.override.yml merges with docker-compose.yml
services:
  web:
    environment:
      DEBUG: "true"
```

**What we adopt**: Override files that merge with defaults.

### Terraform Modules DX

```hcl
module "database" {
  source = "terraform-aws-modules/rds/aws"

  # Override defaults
  instance_class = "db.t3.large"
}
```

**What we adopt**: Packages as "modules" with overridable variables.

### Helm Charts DX

```yaml
# values.yaml overrides chart defaults
grafana:
  enabled: false

prometheus:
  resources:
    requests:
      memory: "512Mi"
```

**What we adopt**: `enabled: true/false` pattern, deep merge of config.

---

## Success Metrics

1. **Time to first lakehouse**: < 5 minutes from `pip install` to running services
2. **Lines of config for common case**: 2 lines (name + description)
3. **Discoverability**: Users can find available services via `phlo plugin search`
4. **Override success rate**: 90% of customizations achievable via `phlo.yaml`
5. **Error clarity**: Every error message includes a suggested fix

---

## Next Steps

See [implementation-roadmap.md](./implementation-roadmap.md) for the technical plan to achieve these goals.
