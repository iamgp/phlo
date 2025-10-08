# Data Lakehouse Documentation

## Overview

Comprehensive documentation for the Cell & Gene Therapy Data Lakehouse platform.

## Quick Links

### Getting Started
- [Architecture Overview](../readme.md)
- [Setup Guide](../ASSET_BASED_ARCHITECTURE.md)
- [Airbyte Setup](../AIRBYTE_SETUP.md)

### Component Documentation
- [PostgreSQL](./components/postgres.md) - Metadata & marts database
- [MinIO](./components/minio.md) - S3-compatible object storage
- [DuckDB](./components/duckdb.md) - Analytical query engine
- [dbt](./components/dbt.md) - Data transformation tool
- [Dagster](./components/dagster.md) - Orchestration & asset management
- [Superset](./components/superset.md) - BI & dashboards
- [Marquez](./components/marquez.md) - Data lineage tracking

### Integration Guides
- [End-to-End Data Flow](./integrations/data-flow.md) - Complete pipeline walkthrough
- [Dagster + dbt](./integrations/dagster-dbt.md) - Asset-based dbt orchestration

### Platform URLs
- **Dagster UI**: http://localhost:3000
- **Superset**: http://localhost:8088 (admin/admin123)
- **Marquez API**: http://localhost:5555
- **Marquez Web**: http://localhost:3002
- **MinIO Console**: http://localhost:9001 (minio/minio999)
- **PostgreSQL**: localhost:5432 (lake/lakepass)

## Architecture

### Component Stack
```
┌─────────────────────────────────────────┐
│           Superset (BI Layer)            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    PostgreSQL (Analytics Marts)         │
└────────────────▲────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│  dbt + DuckDB (Transformation Layer)    │
│  • Staging (views)                      │
│  • Curated (tables)                     │
└────────────────▲────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│     MinIO (Data Lake Storage)           │
│     • Raw parquet files                 │
│     • S3-compatible API                 │
└────────────────▲────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│  Airbyte (Optional - Data Ingestion)    │
└─────────────────────────────────────────┘

         All orchestrated by Dagster
         All lineage tracked in Marquez
```

### Data Flow Layers

1. **Ingestion**: Airbyte → MinIO (`/raw/`)
2. **Staging**: DuckDB views over raw parquet
3. **Curated**: DuckDB tables with business logic
4. **Marts**: Postgres tables for BI
5. **Visualization**: Superset dashboards
6. **Lineage**: Marquez tracking

## Core Concepts

### Asset-Based Orchestration
Instead of running jobs, we materialize **assets** - discrete data objects with dependencies.

**Assets**:
- `raw_bioreactor_data` - Raw file validation
- `dbt_staging_models` - Cleaned data views
- `dbt_curated_models` - Business logic tables
- `dbt_postgres_marts` - Analytics marts

**Benefits**:
- Visual lineage graph
- Selective execution
- Better observability
- Automatic dependency resolution

### Dual-Database Pattern
- **DuckDB**: Fast analytical transformations on parquet
- **Postgres**: Persistent marts for concurrent BI access

Why both?
- DuckDB excels at parquet queries and aggregations
- Postgres excels at serving dashboards and concurrent users
- dbt bridges them seamlessly

### OpenLineage Integration
Every component emits lineage events to Marquez:
- Track data origin to dashboard
- Impact analysis for changes
- Compliance and audit trails

## Common Workflows

### 1. Daily Pipeline (Automated)
```
02:00 AM - Dagster `nightly_pipeline` schedule triggers
02:01 AM - dbt staging models run (DuckDB views)
02:05 AM - dbt curated models build (DuckDB tables)
02:10 AM - dbt postgres marts materialize
02:15 AM - Pipeline complete, dashboards show fresh data
```

### 2. Manual Refresh
```bash
# Full pipeline
docker compose exec dagster-web dagster asset materialize --select '*'

# Specific layer
docker compose exec dagster-web dagster asset materialize --select dbt_curated_models
```

### 3. Add New Data Source
1. Configure Airbyte connection (optional)
2. Land parquet in `/data/lake/raw/{source}/`
3. Create dbt staging model `stg_{source}.sql`
4. Add Dagster asset in `dagster/assets/`
5. Join in curated layer

### 4. Create Dashboard
1. dbt: Build mart in `marts_postgres/`
2. Dagster: Materialize `dbt_postgres_marts`
3. Superset: Add dataset from `marts.{mart_name}`
4. Build charts and dashboard

## Development

### Local Setup
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f dagster-webserver

# Access containers
docker compose exec dagster-web bash
docker compose exec postgres psql -U lake -d lakehouse
```

### Making Changes

**dbt Models**:
1. Edit model in `dbt/models/`
2. Run locally: `dbt run --select {model}`
3. Commit changes
4. Dagster auto-reloads

**Dagster Assets**:
1. Edit asset in `dagster/assets/`
2. Restart: `docker compose restart dagster-webserver`
3. View in UI: http://localhost:3000

**Superset Dashboards**:
1. Create in UI at http://localhost:8088
2. Export dashboard JSON
3. Commit to repo (optional)

### Testing
```bash
# dbt tests
docker compose exec dagster-web dbt test

# Dagster asset dry-run
docker compose exec dagster-web dagster asset materialize --select {asset} --dry-run

# Query validation
docker compose exec postgres psql -U lake -d lakehouse -c "SELECT count(*) FROM marts.mart_bioreactor_overview"
```

## Monitoring

### Dagster UI (http://localhost:3000)
- **Assets**: View all assets and lineage
- **Runs**: Execution history and logs
- **Schedules**: Manage automated runs

### Marquez UI (http://localhost:3002)
- **Lineage Graph**: Visual data flow
- **Datasets**: All tables and files
- **Jobs**: Transformation history

### Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs dagster-webserver -f
docker compose logs postgres -f
```

## Troubleshooting

### Services Won't Start
```bash
docker compose ps                    # Check status
docker compose logs {service} -f     # View logs
docker compose down && docker compose up -d  # Restart
```

### Assets Not Materializing
1. Check Dagster logs
2. Verify dbt can connect: `dbt debug`
3. Test dbt directly: `dbt run --select {model}`

### Dashboards Show Old Data
1. Check dbt marts: `SELECT max(batch_start) FROM marts.mart_bioreactor_overview`
2. Re-materialize marts: Dagster UI → `dbt_postgres_marts` → Materialize
3. Clear Superset cache: Dashboard → Force Refresh

### Lineage Not Showing
1. Verify Marquez running: `docker compose ps marquez`
2. Check OpenLineage URL in Dagster: `docker compose exec dagster-web env | grep OPENLINEAGE`
3. Re-run pipeline to emit events

## Best Practices

1. **Data Quality**: Add dbt tests for all critical models
2. **Naming**: Use prefixes (stg_, int_, dim_, fact_, mart_)
3. **Documentation**: Document all models and columns in dbt
4. **Lineage**: Always emit OpenLineage events
5. **Monitoring**: Set up alerts for pipeline failures
6. **Performance**: Partition large tables by date/batch
7. **Security**: Use RLS in Superset for multi-tenant data

## Support

### Documentation
- [Component Docs](./components/) - Individual tool documentation
- [Integration Guides](./integrations/) - How components work together
- [Guides](./guides/) - Best practices and patterns

### Common Issues
- [Troubleshooting Guide](./guides/troubleshooting.md) (coming soon)
- [FAQ](./guides/faq.md) (coming soon)

### External Resources
- [Dagster Docs](https://docs.dagster.io)
- [dbt Docs](https://docs.getdbt.com)
- [DuckDB Docs](https://duckdb.org/docs)
- [Superset Docs](https://superset.apache.org/docs)
- [OpenLineage Spec](https://openlineage.io/docs)

## Contributing

### Adding Documentation
1. Create markdown file in appropriate folder:
   - `docs/components/` - Individual tools
   - `docs/integrations/` - How tools work together
   - `docs/guides/` - How-to guides
2. Add link to this README
3. Submit PR

### Improving Platform
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit PR with description

## License

[Add your license here]

## Contact

[Add contact information]
