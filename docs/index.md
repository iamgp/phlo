# Phlo Documentation

Welcome to Phlo - a modern data lakehouse platform combining Apache Iceberg, Project Nessie, Trino, dbt, and Dagster.

## What is Phlo?

Phlo is a decorator-driven data lakehouse framework that reduces boilerplate by 74% while providing:

- Write-Audit-Publish pattern with Git-like branching
- Type-safe data quality with automatic validation
- Production-ready patterns out of the box
- Schema-first development with Pandera

## Quick Start

```bash
# Install and start
git clone https://github.com/iamgp/phlo.git
cd phlo
cp .env.example .env
phlo services start

# Materialize example pipeline
phlo materialize dlt_glucose_entries
```

## Quick Links

- **New to Phlo?** Start with the [Installation Guide](getting-started/installation.md) then [Core Concepts](getting-started/core-concepts.md)
- **Build pipelines:** Follow the [Developer Guide](guides/developer-guide.md)
- **Production deployment:** Check the [Operations Guide](operations/operations-guide.md)
- **Troubleshoot issues:** See [Troubleshooting](operations/troubleshooting.md)

## Documentation Structure

### Getting Started
Essential guides for new users:

- [Installation Guide](getting-started/installation.md) - Complete installation instructions
- [Quickstart Guide](getting-started/quickstart.md) - Get running in 10 minutes
- [Core Concepts](getting-started/core-concepts.md) - Understand Phlo's architecture and patterns

### Guides
In-depth tutorials and how-tos:

- [Developer Guide](guides/developer-guide.md) - Master decorators and workflow development
- [Service Packages](guides/service-packages.md) - Installable infrastructure services
- [Workflow Development](guides/workflow-development.md) - Build complete data pipelines
- [Data Modeling](guides/data-modeling.md) - Bronze/Silver/Gold architecture
- [dbt Development](guides/dbt-development.md) - SQL transformations
- [Dagster Assets](guides/dagster-assets.md) - Orchestration patterns
- [GitHub Workflow](guides/github-workflow.md) - Git branching and CI/CD

### Setup
Configure additional services:

- [OpenMetadata](setup/openmetadata.md) - Data catalog and governance
- [PostgREST](setup/postgrest.md) - REST API from PostgreSQL
- [Hasura](setup/hasura.md) - GraphQL API
- [Observability](setup/observability.md) - Monitoring with Grafana

### Reference
Technical documentation:

- [CLI Reference](reference/cli-reference.md) - Complete command-line interface guide
- [Configuration Reference](reference/configuration-reference.md) - Environment variables and settings
- [Architecture](reference/architecture.md) - System design and components
- [API Reference](reference/api.md) - REST and GraphQL APIs
- [DuckDB Queries](reference/duckdb-queries.md) - Ad-hoc analysis
- [Common Errors](reference/common-errors.md) - Error messages explained

### Operations
Production operations and maintenance:

- [Operations Guide](operations/operations-guide.md) - Daily operations, backups, scaling, security
- [Troubleshooting](operations/troubleshooting.md) - Debug common issues
- [Best Practices](operations/best-practices.md) - Production patterns
- [Testing Guide](operations/testing.md) - Testing strategies

### Blog
Tutorial series and deep dives:

- See [blog/](blog/) for the complete 13-part article series

## Learning Paths

### Path 1: Complete Beginner to First Pipeline
```
1. getting-started/installation.md        (Install Phlo)
2. getting-started/core-concepts.md       (Understand architecture)
3. getting-started/quickstart.md          (Run first pipeline)
4. guides/developer-guide.md              (Build custom workflows)
5. operations/troubleshooting.md          (Fix issues)
```
**Outcome:** Working data pipeline with custom ingestion and quality checks

### Path 2: Developer to Production Expert
```
1. getting-started/core-concepts.md       (Understand patterns)
2. guides/developer-guide.md              (Master decorators)
3. reference/cli-reference.md             (Learn CLI tools)
4. guides/dbt-development.md              (SQL transformations)
5. operations/operations-guide.md         (Production operations)
6. setup/observability.md                 (Monitoring)
```
**Outcome:** Production-ready pipelines with monitoring and automation

### Path 3: Quick Setup to Running System
```
1. getting-started/installation.md        (Install)
2. getting-started/quickstart.md          (Start services)
3. reference/configuration-reference.md   (Configure)
4. operations/troubleshooting.md          (Debug)
```
**Outcome:** Running Phlo instance ready for development

## Getting Help

1. **Search this documentation** - Use your editor's search
2. **Check troubleshooting** - [operations/troubleshooting.md](operations/troubleshooting.md)
3. **Review common errors** - [reference/common-errors.md](reference/common-errors.md)
4. **Official documentation:**
   - [Dagster](https://docs.dagster.io)
   - [dbt](https://docs.getdbt.com)
   - [Trino](https://trino.io/docs)
   - [Iceberg](https://iceberg.apache.org/docs)
   - [Nessie](https://projectnessie.org/docs/)

## Contributing

Phlo is open source. Contributions welcome!

- Report bugs via GitHub Issues
- Submit improvements via Pull Requests
- See [guides/github-workflow.md](guides/github-workflow.md) for workflow

## Key Features

### Decorator-Driven Development
Reduce boilerplate by 74% with `@phlo.ingestion` and `@phlo.quality` decorators.

### Write-Audit-Publish Pattern
Automated branch lifecycle with quality gates and auto-promotion to production.

### Schema-First Development
Pandera schemas auto-generate Iceberg schemas and enforce validation.

### Production-Ready
Built-in monitoring, alerting, backups, and disaster recovery patterns.

---

**Version:** 2.0 | **Last Updated:** 2025-12-06
