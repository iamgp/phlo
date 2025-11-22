# Phlo Documentation

Welcome to Phlo - a modern data lakehouse platform combining Apache Iceberg, Project Nessie, Trino, dbt, and Dagster.

## Quick Links

- **New to Phlo?** Start with the [Quickstart Guide](getting-started/quickstart.md)
- **Understand the concepts:** Read the [Beginner's Guide](getting-started/beginners-guide.md)
- **Build pipelines:** Follow the [Workflow Development Guide](guides/workflow-development.md)

## Documentation Structure

### 🚀 Getting Started
Essential guides for new users:

- [Quickstart Guide](getting-started/quickstart.md) - Get Phlo running in 10 minutes
- [Beginner's Guide](getting-started/beginners-guide.md) - Core concepts and architecture explained

### 📚 Guides
In-depth tutorials and how-tos:

- [Workflow Development](guides/workflow-development.md) - Build complete data pipelines
- [Data Modeling](guides/data-modeling.md) - Bronze/Silver/Gold architecture
- [Dagster Assets](guides/dagster-assets.md) - Master orchestration
- [dbt Development](guides/dbt-development.md) - SQL transformations
- [GitHub Workflow](guides/github-workflow.md) - Git branching and CI/CD

### ⚙️ Setup
Configure additional services:

- [OpenMetadata](setup/openmetadata.md) - Data catalog and governance
- [Hasura](setup/hasura.md) - GraphQL API
- [Observability](setup/observability.md) - Monitoring with Grafana

### 📖 Reference
Technical documentation:

- [API Reference](reference/api.md) - REST and GraphQL APIs
- [Architecture](reference/architecture.md) - System design
- [Configuration](reference/configuration.md) - Environment variables
- [DuckDB Queries](reference/duckdb-queries.md) - Ad-hoc analysis
- [Common Errors](reference/common-errors.md) - Error messages explained

### 🔧 Operations
Production best practices:

- [Troubleshooting](operations/troubleshooting.md) - Debug common issues
- [Best Practices](operations/best-practices.md) - Production patterns
- [Testing Guide](operations/testing.md) - Testing strategies

### 📝 Blog
Tutorial series and deep dives:

- See [blog/](blog/) for the complete article series

## Learning Paths

### Path 1: Complete Beginner → First Pipeline
```
1. getting-started/beginners-guide.md     (Understand concepts)
2. getting-started/quickstart.md          (Get Phlo running)
3. guides/workflow-development.md         (Build your first pipeline)
4. operations/troubleshooting.md          (Fix issues)
```
**Time:** 4-6 hours | **Outcome:** Working data pipeline

### Path 2: Data Engineer → Production Expert
```
1. guides/data-modeling.md                (Learn architecture)
2. guides/dagster-assets.md               (Master orchestration)
3. guides/dbt-development.md              (Master transformations)
4. operations/best-practices.md           (Production patterns)
5. setup/observability.md                 (Monitoring)
```
**Time:** 8-10 hours | **Outcome:** Production-ready pipelines

### Path 3: Quick Setup → Running System
```
1. getting-started/quickstart.md          (Start services)
2. reference/configuration.md             (Configure)
3. operations/troubleshooting.md          (Debug issues)
```
**Time:** 1-2 hours | **Outcome:** Running Phlo instance

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

---

**Version:** 1.0 | **Last Updated:** 2025-11-21
