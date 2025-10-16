# Apache Superset (BI & Dashboards)

## Overview

Superset provides business intelligence and data visualization capabilities, connecting to the Postgres marts to deliver interactive dashboards and reports.

## Access

**URL**: http://localhost:8088
**Username**: `admin`
**Password**: `admin123`

## Architecture

### Container
- **Image**: `apache/superset:latest` + custom init
- **Port**: `8088`
- **Database**: Uses Postgres for metadata and connects to marts

### Initialization
Custom `superset_init.sh` script runs on startup:
1. Creates admin user
2. Runs database migrations
3. Initializes Superset

## Configuration

### Database Connection
Superset connects to Postgres marts:

**Connection String**:
```
postgresql://lake:lakepass@postgres:5432/lakehouse
```

### Adding Database in UI
1. Navigate to Settings → Database Connections
2. Click "+ Database"
3. Select "PostgreSQL"
4. Enter details:
   - **Host**: `postgres`
   - **Port**: `5432`
   - **Database**: `lakehouse`
   - **Username**: `lake`
   - **Password**: `lakepass`
5. Test Connection
6. Save

## Creating Datasets

### From Database Tables
1. Go to Data → Datasets
2. Click "+ Dataset"
3. Select:
   - **Database**: PostgreSQL (lakehouse)
   - **Schema**: `marts`
   - **Table**: `mart_bioreactor_overview`
4. Click "Add"

### SQL Lab Queries
1. Navigate to SQL → SQL Lab
2. Write custom query:
```sql
SELECT
  batch_id,
  equipment_id,
  batch_start,
  avg_value,
  tag
FROM marts.mart_bioreactor_overview
WHERE batch_start >= CURRENT_DATE - INTERVAL '30 days'
```
3. Save as Dataset

## Building Charts

### Example: Batch Trend Line
1. Go to Charts → "+ Chart"
2. Select Dataset: `mart_bioreactor_overview`
3. Choose Visualization: "Line Chart"
4. Configure:
   - **X-Axis**: `batch_start` (temporal)
   - **Y-Axis**: `avg_value`
   - **Group By**: `tag`
   - **Filters**: Last 30 days
5. Run Query
6. Save Chart

### Example: Equipment Comparison
1. Chart Type: "Bar Chart"
2. Configuration:
   - **X-Axis**: `equipment_id`
   - **Y-Axis**: `avg_value`
   - **Color**: `tag`
3. Save

## Creating Dashboards

### New Dashboard
1. Go to Dashboards → "+ Dashboard"
2. Enter Name: "Bioreactor Overview"
3. Drag charts from sidebar onto canvas
4. Arrange and resize
5. Add filters:
   - **Time Range**: Date filter
   - **Equipment**: Dropdown filter
   - **Tag**: Multi-select filter
6. Save Dashboard

### Dashboard Filters
```
Time Filter:
- Column: batch_start
- Type: Time Range
- Default: Last 30 days

Equipment Filter:
- Column: equipment_id
- Type: Select
- Multiple: Yes
```

## Data Refresh Strategy

### Real-Time (Queries)
Superset queries Postgres directly, so data is as fresh as the marts:
- **Source**: `marts.mart_bioreactor_overview`
- **Freshness**: Updated by dbt nightly (2 AM)
- **Latency**: ~1 second query time

### Caching
Configure chart cache:
1. Edit Chart → Advanced → Cache Timeout
2. Set to `3600` (1 hour) for performance
3. Force refresh with "Force Refresh" button

### Async Queries
For long-running queries:
1. Settings → Advanced → Enable Async Query
2. Queries run in background
3. Results cached and displayed when ready

## User Management

### Create Users
1. Settings → List Users
2. Click "+ User"
3. Fill details:
   - **Username**: `analyst1`
   - **First/Last Name**: Analyst One
   - **Email**: analyst1@company.com
   - **Role**: Alpha (full access) or Gamma (limited)
4. Save

### Roles
- **Admin**: Full access, user management
- **Alpha**: Create charts/dashboards, no user management
- **Gamma**: View-only access to assigned dashboards
- **Public**: Unauthenticated access (if enabled)

### Row-Level Security
Filter data by user:
1. Settings → Row Level Security
2. Add Rule:
   - **Table**: `marts.mart_bioreactor_overview`
   - **Clause**: `site = '{{ current_user_site() }}'`
   - **Roles**: Gamma

## Embedding Dashboards

### Public Access
1. Edit Dashboard → Settings
2. Enable "Published"
3. Copy public URL
4. Embed in iframe:
```html
<iframe
  src="http://localhost:8088/superset/dashboard/1/?standalone=true"
  width="100%"
  height="600px"
></iframe>
```

### Authenticated Embedding
Use Superset's embedding API with JWT tokens.

## Alerting & Reports

### Scheduled Reports (Superset 2.0+)
1. Go to chart/dashboard
2. Click "..." → Schedule Email Report
3. Configure:
   - **Recipients**: Email addresses
   - **Schedule**: Daily @ 8 AM
   - **Format**: PNG or PDF
4. Save

### Alerts
1. Settings → Alerts & Reports
2. Click "+ Alert"
3. Configure:
   - **Chart**: Select chart
   - **Trigger**: When value > threshold
   - **Recipients**: Email/Slack
4. Save

## Performance Optimization

### 1. Database Indexes
Ensure Postgres marts have indexes:
```sql
-- In Postgres
CREATE INDEX idx_batch_start ON marts.mart_bioreactor_overview(batch_start);
CREATE INDEX idx_equipment ON marts.mart_bioreactor_overview(equipment_id);
CREATE INDEX idx_tag ON marts.mart_bioreactor_overview(tag);
```

### 2. Query Optimization
Use SQL Lab to test queries before charting:
```sql
-- Bad: Full table scan
SELECT * FROM marts.mart_bioreactor_overview;

-- Good: Filtered, indexed columns
SELECT
  batch_id,
  equipment_id,
  avg_value
FROM marts.mart_bioreactor_overview
WHERE batch_start >= CURRENT_DATE - INTERVAL '30 days'
  AND equipment_id = 'BR-001';
```

### 3. Materialized Views (in Postgres)
For complex queries, create materialized views:
```sql
-- In Postgres
CREATE MATERIALIZED VIEW marts.mv_daily_summary AS
SELECT
  date_trunc('day', batch_start) as day,
  equipment_id,
  tag,
  avg(avg_value) as daily_avg
FROM marts.mart_bioreactor_overview
GROUP BY 1, 2, 3;

-- Refresh nightly (add to dbt or cron)
REFRESH MATERIALIZED VIEW marts.mv_daily_summary;
```

### 4. Superset Cache
Enable caching in `superset_config.py`:
```python
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 60 * 60,  # 1 hour
    'CACHE_KEY_PREFIX': 'superset_',
}
```

## Custom Visualizations

### Install Plugins
```bash
# Access Superset container
docker compose exec superset bash

# Install viz plugin
pip install superset-viz-plugins

# Restart
docker compose restart superset
```

### Custom D3.js Charts
1. Write D3 code in Superset UI
2. Use in "Custom Visualization" chart type

## Troubleshooting

### Can't Connect to Database
```bash
# Test from Superset container
docker compose exec superset bash
psql -h postgres -U lake -d lakehouse

# Check network
docker network inspect cascade_default
```

### Charts Not Loading
1. Check browser console for errors
2. Verify query in SQL Lab
3. Check Superset logs:
```bash
docker compose logs superset
```

### Slow Queries
```sql
-- Check query plan in Postgres
EXPLAIN ANALYZE
SELECT * FROM marts.mart_bioreactor_overview
WHERE batch_start >= CURRENT_DATE - INTERVAL '30 days';
```

### Admin User Reset
```bash
docker compose exec superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password admin123
```

## Backup & Export

### Export Dashboards
1. Dashboards → Select dashboard
2. Click "..." → Export
3. Downloads JSON file

### Import Dashboards
1. Dashboards → Import
2. Upload JSON file
3. Configure database connections

### Backup Metadata DB
Superset uses Postgres for metadata:
```bash
docker compose exec postgres pg_dump -U lake superset_meta > superset_backup.sql
```

## Integration with Data Pipeline

### Data Flow
```
dbt (Postgres marts) → Superset (queries) → Dashboards
```

### Refresh Pattern
1. **2 AM**: dbt runs via Dagster, updates marts
2. **8 AM**: Superset scheduled reports sent
3. **All day**: Users query fresh data

### Alerting on Data Quality
Create alerts on data quality metrics:
1. Add data quality mart in dbt:
```sql
-- models/marts_postgres/mart_data_quality.sql
SELECT
  current_date as check_date,
  count(*) as total_records,
  count(distinct batch_id) as unique_batches
FROM {{ ref('stg_bioreactor') }}
```

2. In Superset, create alert:
   - **Metric**: `total_records`
   - **Trigger**: `< 1000` (too few records)
   - **Action**: Email data team

## Best Practices

1. **Naming**: Clear chart/dashboard names
2. **Filters**: Add time and dimension filters to dashboards
3. **Performance**: Limit data with WHERE clauses
4. **Caching**: Enable for stable reports
5. **Security**: Use RLS for multi-tenant data
6. **Documentation**: Add descriptions to charts
7. **Colors**: Use consistent color schemes
8. **Testing**: Validate queries in SQL Lab first

## Next Steps

- [Superset + Postgres Integration](../integrations/superset-postgres.md)
- [Dashboard Design Guide](../guides/dashboard-design.md)
- [Alerting Strategy](../guides/alerting-strategy.md)
