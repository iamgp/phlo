# Phlo Packages Reference

Phlo is organized as a modular monorepo. Each package contributes a capability, runtime surface, or operator tool.

Use this section to answer:

- what does this package add to a Phlo stack?
- is it core, optional, or profile-specific?
- which other packages or capabilities does it connect to?

For environment-specific setup of external surfaces such as Hasura, PostgREST, or OpenMetadata, use [Setup](../setup/index.md).

Use [Python Reference](../python-reference/index.mdx) when you need symbol-level docstring and API reference for the package modules themselves.

## Complete Package Index

### Core Framework (1 package)

| Package | Description | Entry Points |
| ------- | ----------- | ------------ |
| **phlo** | Core framework with CLI, plugin system, configuration, and hooks | CLI, hooks, catalogs |

---

### Data Processing & Orchestration (7 packages)

| Package | Description | Category |
|---------|-------------|----------|
| [phlo-dagster](phlo-dagster.md) | Orchestration adapter for Dagster pipelines | Orchestration |
| [phlo-dbt](phlo-dbt.md) | dbt integration for SQL transformations | Transformation |
| [phlo-dlt](phlo-dlt.md) | Data Load Tool integration for data ingestion | Ingestion |
| [phlo-sling](phlo-sling.md) | Sling-based data replication pipelines | Ingestion |
| [phlo-iceberg](phlo-iceberg.md) | Apache Iceberg table format and catalog | Storage |
| [phlo-delta](phlo-delta.md) | Delta Lake table format support | Storage |
| [phlo-pandera](phlo-pandera.md) | Data quality validation with Pandera | Quality |

---

### Query & Analytics (2 packages)

| Package | Description | Features |
|---------|-------------|----------|
| [phlo-trino](phlo-trino.md) | Distributed SQL query engine | Query federation, governance |
| [phlo-clickhouse](phlo-clickhouse.md) | High-performance analytical database | Fast aggregations |

---

### Data Lineage & Metadata (2 packages)

| Package | Description | Integration |
|---------|-------------|-------------|
| [phlo-lineage](phlo-lineage.md) | Data lineage tracking and graph storage | Dagster, dbt |
| [phlo-openmetadata](phlo-openmetadata.md) | Data catalog and governance platform | Nessie, Trino |

---

### Storage & Catalog (4 packages)

| Package | Description | Protocol |
|---------|-------------|----------|
| [phlo-nessie](phlo-nessie.md) | Git-like catalog for Iceberg tables | Nessie API |
| [phlo-postgres](phlo-postgres.md) | PostgreSQL metadata and state store | PostgreSQL |
| [phlo-minio](phlo-minio.md) | S3-compatible object storage | S3 API |
| [phlo-rustfs](phlo-rustfs.md) | High-performance S3-compatible storage | S3 API |

---

### Networking & Proxy (2 packages)

| Package | Description | Use Case |
|---------|-------------|----------|
| [phlo-traefik](phlo-traefik.md) | Reverse proxy with automatic service discovery | Local development URLs |
| [phlo-oauth2-proxy](phlo-oauth2-proxy.md) | OAuth2/OIDC forward-auth gateway | SSO with Traefik |

---

### Observability Stack (7 packages)

| Package | Description | Signal Type |
|---------|-------------|---------------|
| [phlo-clickstack](phlo-clickstack.md) | All-in-one observability (ClickHouse + Grafana) | All-in-one |
| [phlo-otel](phlo-otel.md) | OpenTelemetry trace/metric/log emission | Emission |
| [phlo-alloy](phlo-alloy.md) | OpenTelemetry collector and routing | Collection |
| [phlo-prometheus](phlo-prometheus.md) | Metrics collection and storage | Metrics |
| [phlo-grafana](phlo-grafana.md) | Metrics visualization dashboards | Visualization |
| [phlo-loki](phlo-loki.md) | Log aggregation and querying | Logs |
| [phlo-alerting](phlo-alerting.md) | Alert routing and notification management | Alerting |

---

### API Layer (4 packages)

| Package | Description | Protocol |
|---------|-------------|----------|
| [phlo-api](phlo-api.md) | REST API for Phlo internals | REST |
| [phlo-mcp](phlo-mcp.md) | MCP server for observability and lakehouse operations | MCP |
| [phlo-postgrest](phlo-postgrest.md) | Auto-generated REST API from PostgreSQL | REST |
| [phlo-hasura](phlo-hasura.md) | GraphQL API with real-time subscriptions | GraphQL |

---

### User Interface (3 packages)

| Package | Description | Purpose |
|---------|-------------|---------|
| [phlo-observatory](phlo-observatory.md) | Web UI for data exploration and monitoring | Primary UI |
| [phlo-superset](phlo-superset.md) | Business intelligence and visualization | BI/Reporting |
| [phlo-pgweb](phlo-pgweb.md) | PostgreSQL web administration interface | DB Admin |

---

### Development & Testing (2 packages)

| Package | Description | Use Case |
|---------|-------------|----------|
| [phlo-testing](phlo-testing.md) | Testing utilities, fixtures, and mocks | Development |
| [phlo-core-plugins](phlo-core-plugins.md) | Built-in quality checks and source connectors | Core functionality |

---

### Examples & Templates (1 package)

| Package | Description | Purpose |
|---------|-------------|---------|
| [phlo-observatory-example](phlo-observatory-example.md) | Example Observatory extension plugin | Reference implementation |

---

## Installation Profiles

### Full Installation (Recommended)

Install all default packages:

```bash
uv pip install phlo[defaults]
```

**Includes:** Core framework + dagster, postgres, trino, minio, nessie, iceberg, dlt, dbt, pandera

### Minimal Installation

Core framework only:

```bash
uv pip install phlo
```

### Profile-Based Installation

```bash
# Observability stack (monitoring, logging, tracing)
uv pip install phlo[observability]

# API layer (REST, GraphQL)
uv pip install phlo[api]

# Data catalog (OpenMetadata)
uv pip install phlo[catalog]

# Query engines (Trino + ClickHouse)
uv pip install phlo[query]

# UI layer (Observatory + BI tools)
uv pip install phlo[ui]
```

### Development Installation

For contributors and plugin developers:

```bash
# Clone the repository
git clone https://github.com/phlohouse/phlo.git
cd phlo

# Install with all dev dependencies
uv pip install -e ".[dev]"

# Or install specific packages in editable mode
uv pip install -e ./packages/phlo-dlt -e ./packages/phlo-pandera
```

---

## Plugin Entry Points

All packages register plugins through Python entry points. These are the available entry point groups:

| Entry Point Group | Description | Example Provider |
|-------------------|-------------|------------------|
| `phlo.plugins.services` | Infrastructure service definitions | phlo-postgres, phlo-minio |
| `phlo.sources` | Data source connectors | phlo-core-plugins |
| `phlo.ingestion_providers` | Ingestion system providers | phlo-dlt, phlo-sling |
| `phlo.quality` | Quality check implementations | phlo-core-plugins |
| `phlo.quality_providers` | Quality validation providers | phlo-pandera |
| `phlo.transformation_providers` | Transformation providers | phlo-dbt |
| `phlo.transforms` | Data transformation tools | phlo-dbt |
| `phlo.plugins.catalogs` | Catalog configurations | phlo-nessie, phlo-openmetadata |
| `phlo.orchestrators` | Orchestrator adapters | phlo-dagster |
| `phlo.asset_providers` | Asset definition providers | phlo-dagster, phlo-dbt |
| `phlo.resource_providers` | Resource definition providers | phlo-iceberg, phlo-trino |
| `phlo.cli_commands` | CLI command extensions | phlo-nessie, phlo-dbt |
| `phlo.plugins.hooks` | Event hook handlers | phlo-otel, phlo-alerting |
| `phlo.plugins.observatory` | Observatory UI extensions | phlo-observatory-example |

### Discovering Plugins

```bash
# List all installed plugins
phlo plugin list

# List by type
phlo plugin list --type services
phlo plugin list --type sources
phlo plugin list --type quality

# Get detailed plugin information
phlo plugin info dagster
phlo plugin info pandera
```

---

## Common Package Combinations

### Basic Lakehouse (Minimal)

```bash
uv pip install phlo phlo-dagster phlo-postgres phlo-trino phlo-minio phlo-nessie
```

### Full Pipeline Stack

```bash
uv pip install phlo phlo-dagster phlo-postgres phlo-trino phlo-minio \
  phlo-nessie phlo-iceberg phlo-dlt phlo-dbt phlo-pandera
```

### With Observability

```bash
uv pip install phlo phlo-dagster phlo-postgres phlo-trino phlo-minio \
  phlo-nessie phlo-iceberg phlo-dlt phlo-dbt phlo-pandera \
  phlo-otel phlo-prometheus phlo-grafana phlo-loki phlo-alerting
```

### With API Layer

```bash
uv pip install phlo phlo-dagster phlo-postgres phlo-trino phlo-minio \
  phlo-nessie phlo-iceberg phlo-dlt phlo-dbt phlo-pandera \
  phlo-api phlo-postgrest phlo-hasura
```

### Complete Stack

```bash
uv pip install phlo[defaults] phlo[observability] phlo[api] phlo[catalog] phlo[ui]
```

---

## Package Versioning

All packages share synchronized versioning with the core phlo package. Always keep packages at the same version to ensure compatibility.

```bash
# Check installed versions
pip list | grep phlo

# Example output:
# phlo              0.7.8
# phlo-dagster      0.7.8
# phlo-dbt          0.7.8
# phlo-dlt          0.7.8
```

---

## Creating Custom Packages

Build your own packages that integrate with Phlo:

1. See [Plugin Development Guide](../guides/plugin-development.md) for API details
2. Use [phlo-observatory-example](phlo-observatory-example.md) as a reference
3. Register through entry points for automatic discovery

---

## Next Steps

- [Getting Started](../getting-started/quickstart.md) - Run your first pipeline
- [Plugin Development Guide](../guides/plugin-development.md) - Build custom integrations
- [CLI Reference](../reference/cli-reference.md) - Manage packages and services
- [Architecture Overview](../reference/architecture.md) - Understand the system design
