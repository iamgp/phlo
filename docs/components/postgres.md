# PostgreSQL

## Overview

PostgreSQL serves dual roles in the lakehouse architecture:
1. **Metadata store** - for Dagster, Airbyte, and Marquez
2. **Analytics marts** - optimized tables for BI and dashboards

## Configuration

**Image**: `postgres:16`
**Container**: `pg`
**Port**: `5432`

### Environment Variables
```bash
POSTGRES_USER=lake
POSTGRES_PASSWORD=lakepass
POSTGRES_DB=lakehouse
POSTGRES_PORT=5432
```

## Databases

### 1. `lakehouse` (Primary)
- **Purpose**: Data marts for analytics
- **Schema**: `marts`
- **Access**: Superset, dbt (target: postgres)
- **Tables**:
  - `marts.mart_bioreactor_overview` - aggregated bioreactor metrics
  - Additional marts created by dbt models tagged `mart`

### 2. `airbyte`
- **Purpose**: Airbyte metadata and sync state
- **Created by**: Airbyte on first run
- **Schema**: Internal Airbyte tables

### 3. `marquez`
- **Purpose**: OpenLineage metadata and lineage graph
- **Created by**: Marquez on first run
- **Schema**: Internal Marquez tables

## Data Flow

```
dbt (DuckDB) → dbt run --target postgres → PostgreSQL marts → Superset
```

## Connecting

### From Host Machine
```bash
psql -h localhost -p 5432 -U lake -d lakehouse
# Password: lakepass
```

### From Docker Containers
```bash
# Connection string
postgresql://lake:lakepass@postgres:5432/lakehouse
```

### In dbt profiles.yml
```yaml
postgres:
  type: postgres
  host: postgres
  user: "{{ env_var('POSTGRES_USER') }}"
  password: "{{ env_var('POSTGRES_PASSWORD') }}"
  port: 5432
  dbname: "{{ env_var('POSTGRES_DB') }}"
  schema: marts
```

## Maintenance

### Backup
```bash
docker compose exec postgres pg_dump -U lake lakehouse > backup.sql
```

### Restore
```bash
docker compose exec -T postgres psql -U lake lakehouse < backup.sql
```

### View Tables
```sql
-- List all tables in marts schema
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'marts';
```

## Performance Considerations

### Indexes
dbt automatically creates indexes based on:
- Primary keys defined in schema.yml
- `{{ config(indexes=[...]) }}` in models

### Vacuuming
Postgres auto-vacuum is enabled by default. For manual vacuum:
```sql
VACUUM ANALYZE marts.mart_bioreactor_overview;
```

### Monitoring
```sql
-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'marts'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

## Troubleshooting

### Connection Issues
```bash
# Check if container is healthy
docker compose ps postgres

# View logs
docker compose logs postgres

# Test connection
docker compose exec postgres pg_isready -U lake
```

### Schema Doesn't Exist
```sql
-- Create marts schema if missing
CREATE SCHEMA IF NOT EXISTS marts;
```

### Permission Issues
```sql
-- Grant permissions (run as superuser)
GRANT ALL PRIVILEGES ON SCHEMA marts TO lake;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA marts TO lake;
```
