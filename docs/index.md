# Cascade Documentation Index

Welcome to the Cascade documentation! This guide helps you navigate all available documentation based on your needs and experience level.

---

## 📖 Documentation Overview

### For Complete Beginners

**Start here if you're new to data engineering or Cascade:**

1. **[BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md)** - Start here!
   - What is a data lakehouse?
   - Core concepts explained simply
   - How Cascade works end-to-end
   - Understanding all the technologies
   - Your first look at the platform
   - Common workflows to try

### Building Your First Pipeline

**Step-by-step tutorials for hands-on learning:**

2. **[WORKFLOW_DEVELOPMENT_GUIDE.md](WORKFLOW_DEVELOPMENT_GUIDE.md)**
   - Complete tutorial: Build a weather data pipeline from scratch
   - Creating ingestion assets with DLT
   - Building Bronze/Silver/Gold layers
   - Adding data quality checks
   - Scheduling and automation
   - 10-step guided walkthrough

3. **[../QUICK_START.md](../QUICK_START.md)**
   - Quick setup and installation
   - Get Cascade running in minutes
   - First pipeline execution

### Data Modeling & Architecture

**Design patterns and best practices:**

4. **[DATA_MODELING_GUIDE.md](DATA_MODELING_GUIDE.md)**
   - Bronze/Silver/Gold medallion architecture explained
   - What belongs in each layer
   - Fact vs dimension tables
   - Real-world examples
   - Schema evolution strategies

5. **[architecture.md](architecture.md)** & **[../ARCHITECTURE.md](../ARCHITECTURE.md)**
   - System architecture overview
   - Component diagrams
   - Design principles
   - Technology stack details

### Technology Deep-Dives

**Master specific technologies:**

6. **[DAGSTER_ASSETS_TUTORIAL.md](DAGSTER_ASSETS_TUTORIAL.md)**
   - Complete guide to asset-based orchestration
   - Dependencies and data flow
   - Resources and configuration
   - Partitions (daily, hourly, multi-dimensional)
   - Schedules and sensors
   - Advanced patterns and troubleshooting

7. **[DBT_DEVELOPMENT_GUIDE.md](DBT_DEVELOPMENT_GUIDE.md)**
   - dbt fundamentals
   - Sources, models, and refs
   - Tests and documentation
   - Macros and Jinja templating
   - Incremental models
   - Best practices

### Operations & Troubleshooting

**When things go wrong:**

8. **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)**
   - Services won't start
   - Dagster issues
   - dbt compilation errors
   - Query performance problems
   - Data quality debugging
   - Step-by-step debugging techniques

9. **[BEST_PRACTICES_GUIDE.md](BEST_PRACTICES_GUIDE.md)**
   - General principles (idempotency, immutability)
   - Code organization
   - Data quality patterns
   - Performance optimization
   - Security best practices
   - Testing strategies
   - Production deployment checklist

### Specific Features

**Specialized topics:**

10. **[API.md](API.md)**
    - REST API documentation
    - Authentication with JWT
    - Available endpoints
    - Example requests

11. **[HASURA_SETUP.md](HASURA_SETUP.md)**
    - GraphQL API setup
    - Connecting to PostgreSQL
    - Creating queries and subscriptions

12. **[OBSERVABILITY.md](OBSERVABILITY.md)**
    - Prometheus metrics
    - Grafana dashboards
    - Log aggregation with Loki
    - Setting up alerts

13. **[configuration.md](configuration.md)**
    - Environment variables
    - Service configuration
    - Connection strings
    - Feature flags

14. **[duckdb-iceberg-queries.md](duckdb-iceberg-queries.md)**
    - Querying Iceberg tables with DuckDB
    - Ad-hoc analytics
    - Local development queries

15. **[github_workflow_guide.md](github_workflow_guide.md)**
    - Git branching strategy
    - Pull request workflow
    - CI/CD integration

16. **[../NESSIE_WORKFLOW.md](../NESSIE_WORKFLOW.md)**
    - Data branching with Nessie
    - Branch management
    - Merging and tagging
    - Time travel queries

---

## 🎯 Learning Paths

### Path 1: Complete Beginner → First Pipeline

```
1. BEGINNERS_GUIDE.md          (Understand the concepts)
2. QUICK_START.md               (Get Cascade running)
3. WORKFLOW_DEVELOPMENT_GUIDE.md (Build your first pipeline)
4. TROUBLESHOOTING_GUIDE.md    (Fix issues that arise)
```

**Time:** 4-6 hours
**Outcome:** Working data pipeline end-to-end

### Path 2: Data Engineer → Production Expert

```
1. DATA_MODELING_GUIDE.md      (Learn architecture patterns)
2. DAGSTER_ASSETS_TUTORIAL.md  (Master orchestration)
3. DBT_DEVELOPMENT_GUIDE.md    (Master transformations)
4. BEST_PRACTICES_GUIDE.md     (Production patterns)
5. OBSERVABILITY.md            (Monitoring setup)
```

**Time:** 8-10 hours
**Outcome:** Production-ready pipelines with monitoring

### Path 3: Troubleshooter → Expert

```
1. ARCHITECTURE.md             (Understand the system)
2. TROUBLESHOOTING_GUIDE.md    (Debug common issues)
3. OBSERVABILITY.md            (Monitor health)
4. NESSIE_WORKFLOW.md          (Data versioning)
```

**Time:** 3-4 hours
**Outcome:** Can debug and optimize Cascade

---

## 📚 Quick Reference

### I want to...

**Understand Cascade:**
- → [BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md)
- → [architecture.md](architecture.md)

**Build a pipeline:**
- → [WORKFLOW_DEVELOPMENT_GUIDE.md](WORKFLOW_DEVELOPMENT_GUIDE.md)
- → [DATA_MODELING_GUIDE.md](DATA_MODELING_GUIDE.md)

**Work with Dagster:**
- → [DAGSTER_ASSETS_TUTORIAL.md](DAGSTER_ASSETS_TUTORIAL.md)

**Work with dbt:**
- → [DBT_DEVELOPMENT_GUIDE.md](DBT_DEVELOPMENT_GUIDE.md)

**Fix an issue:**
- → [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)

**Set up monitoring:**
- → [OBSERVABILITY.md](OBSERVABILITY.md)

**Use the API:**
- → [API.md](API.md)

**Deploy to production:**
- → [BEST_PRACTICES_GUIDE.md](BEST_PRACTICES_GUIDE.md)

---

## 🆘 Getting Help

**In order of preference:**

1. **Search this documentation** - Use Ctrl+F or your editor's search
2. **Check the troubleshooting guide** - [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
3. **Official docs:**
   - Dagster: https://docs.dagster.io
   - dbt: https://docs.getdbt.com
   - Trino: https://trino.io/docs
   - Iceberg: https://iceberg.apache.org/docs
4. **Open an issue** - Describe your problem with logs and code

---

## 📝 Documentation Status

| Document | Status | Last Updated | For |
|----------|--------|--------------|-----|
| BEGINNERS_GUIDE.md | ✅ Current | 2025-11 | New users |
| WORKFLOW_DEVELOPMENT_GUIDE.md | ✅ Current | 2025-11 | Tutorials |
| DATA_MODELING_GUIDE.md | ✅ Current | 2025-11 | Architecture |
| DAGSTER_ASSETS_TUTORIAL.md | ✅ Current | 2025-11 | Orchestration |
| DBT_DEVELOPMENT_GUIDE.md | ✅ Current | 2025-11 | Transformations |
| TROUBLESHOOTING_GUIDE.md | ✅ Current | 2025-11 | Debugging |
| BEST_PRACTICES_GUIDE.md | ✅ Current | 2025-11 | Production |
| API.md | ✅ Current | 2025 | API usage |
| OBSERVABILITY.md | ✅ Current | 2025 | Monitoring |
| architecture.md | ✅ Current | 2025 | Architecture |

---

## 🔄 Documentation Maintenance

**Contributing to docs:**
1. All documentation in `docs/` folder
2. Use Markdown format
3. Include code examples
4. Link between related docs
5. Update this index when adding new docs

**Style guide:**
- Use clear headings and table of contents
- Include real code examples (not pseudocode)
- Explain the "why" not just the "how"
- Link to related documentation
- Include troubleshooting sections

---

**Last updated:** 2025-11-06
**Version:** 1.0
**Maintained by:** Cascade Team
