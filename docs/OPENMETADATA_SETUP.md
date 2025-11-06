# OpenMetadata Data Catalog Setup Guide

## Overview

OpenMetadata is an open-source data catalog that provides a unified platform for data discovery, governance, and collaboration. This guide explains how to set up and use OpenMetadata with Cascade to enable self-service data discovery.

## What is a Data Catalog?

A data catalog is a searchable inventory of your data assets that helps users:

- **Discover** datasets through search and browsing
- **Understand** data through metadata, descriptions, and lineage
- **Access** data through multiple interfaces (SQL, APIs, dashboards)
- **Govern** data with ownership, tags, and quality metrics

## Why OpenMetadata for Cascade?

OpenMetadata integrates seamlessly with Cascade's tech stack:

- ✅ **Trino connector** - Auto-discovers Iceberg tables
- ✅ **Modern UI** - Intuitive search and browsing experience
- ✅ **Active development** - Regular updates and improvements
- ✅ **Simple architecture** - MySQL + Elasticsearch (6GB RAM required)
- ✅ **Open source** - No licensing costs

## Architecture

```
┌─────────────────────────────────────────────┐
│         OpenMetadata Server (UI)           │
│         http://localhost:10020              │
└─────────────┬───────────────────────────────┘
              │
       ┌──────┴──────┐
       │             │
┌──────▼──────┐ ┌───▼────────────┐
│    MySQL    │ │ Elasticsearch  │
│  (metadata) │ │   (search)     │
└─────────────┘ └────────────────┘
       │
       │ Ingests metadata from:
       │
┌──────▼──────────────────────────────┐
│  Trino → Iceberg Tables (Nessie)   │
│  - bronze.entries_cleaned          │
│  - silver.glucose_daily_stats      │
│  - gold.dim_date                   │
│  - marts.glucose_analytics_mart    │
└────────────────────────────────────┘
```

## Quick Start

### 1. Start OpenMetadata Services

```bash
# Start the data catalog stack
make up-catalog

# Check health status
make health-catalog
```

**Expected output:**
```
=== Data Catalog Health Check ===
OpenMetadata:
  Ready
  UI: http://localhost:10020
  Default credentials: admin / admin
MySQL:
  Ready
Elasticsearch:
  Ready
```

### 2. Access OpenMetadata UI

```bash
# Open in browser
make catalog
# Or manually visit: http://localhost:10020
```

**Default credentials:**
- Username: `admin`
- Password: `admin`

> ⚠️ **Security Note**: Change the default password in production by updating `OPENMETADATA_ADMIN_PASSWORD` in `.env`

### 3. First Login

1. Navigate to http://localhost:10020
2. Login with `admin` / `admin`
3. Complete the welcome tour (optional)
4. You'll see the empty catalog dashboard

## Connecting Cascade Data Sources

### Step 1: Add Trino Connection

1. Click **Settings** (gear icon) in the top-right
2. Navigate to **Services** → **Databases**
3. Click **Add Service**
4. Select **Trino** as the database type
5. Configure the connection:

```yaml
Name: cascade-trino
Description: Cascade Lakehouse Trino Query Engine
Host: trino
Port: 8080
Username: cascade
Catalog: iceberg
```

6. Click **Test Connection** → Should show success
7. Click **Save**

### Step 2: Configure Metadata Ingestion

1. In the Trino service page, click **Add Ingestion**
2. Select **Metadata Ingestion**
3. Configure:

```yaml
Name: cascade-iceberg-metadata
Include Schemas: bronze, silver, gold, marts, raw
Include Tables: .*
```

4. Set schedule (optional): Daily at 2:00 AM
5. Click **Save**

### Step 3: Run Initial Ingestion

1. Click **Run** on the ingestion pipeline
2. Wait 1-2 minutes for completion
3. Navigate to **Explore** → **Tables**
4. You should see all your Iceberg tables!

## Discovered Data Assets

After ingestion, you'll see:

### Bronze Layer (Staging)
- `bronze.entries_cleaned` - CGM entries with type conversions
- `bronze.device_status_cleaned` - Device status events

### Silver Layer (Facts)
- `silver.glucose_daily_stats` - Daily glucose aggregations
- `silver.glucose_weekly_stats` - Weekly glucose aggregations

### Gold Layer (Dimensions)
- `gold.dim_date` - Date dimension table

### Marts (BI-Ready)
- `marts.glucose_analytics_mart` - Published to Postgres for Superset

## Using the Data Catalog

### Search for Data

1. Use the search bar at the top
2. Search by:
   - Table name: `glucose_daily_stats`
   - Column name: `mean_glucose`
   - Description keywords: `"blood sugar"`
   - Tags: `#glucose` (after adding tags)

### View Table Details

Click on any table to see:

- **Schema**: Column names, types, descriptions
- **Sample Data**: Preview of actual data
- **Lineage**: Visual graph showing upstream/downstream tables
- **Queries**: Recent SQL queries (if query log enabled)
- **Usage**: Access patterns and popularity

### Add Documentation

1. Click on a table (e.g., `silver.glucose_daily_stats`)
2. Click **Edit** (pencil icon)
3. Add description:

```markdown
## Description
Daily aggregated glucose statistics including mean, standard deviation,
time in range, and estimated A1C.

## Update Schedule
Updated daily at 2:00 AM UTC via Dagster pipeline.

## Business Logic
- `time_in_range_pct`: Percentage of readings between 70-180 mg/dL
- `estimated_a1c`: Calculated using formula: (mean_glucose + 46.7) / 28.7
```

4. Add column descriptions:
   - `date`: Measurement date (partition key)
   - `mean_glucose`: Daily average glucose in mg/dL
   - `std_glucose`: Standard deviation of glucose readings
   - `time_in_range_pct`: % of time in target range (70-180 mg/dL)

5. Click **Save**

### Add Tags

1. Click on a table
2. Click **Add Tag**
3. Use built-in tags or create custom:
   - `PII.None` - No personal information
   - `Tier.Bronze` / `Tier.Silver` / `Tier.Gold`
   - Create custom: `Healthcare`, `CGM`, `Analytics`

### Set Ownership

1. Click on a table
2. Click **Add Owner**
3. Select user or team (create teams in Settings)

## Data Lineage

OpenMetadata can show visual lineage graphs:

```
entries_raw (raw)
    ↓
entries_cleaned (bronze) ← dbt model
    ↓
glucose_daily_stats (silver) ← dbt model
    ↓
glucose_analytics_mart (mart) ← Trino publish
    ↓
Superset Dashboard: "CGM Overview"
```

### Enable Lineage Tracking

Lineage is automatically extracted from:
- **dbt models** - Add dbt ingestion pipeline
- **SQL queries** - Enable query log ingestion

To add dbt lineage:

1. **Settings** → **Services** → **Pipeline Services**
2. **Add Service** → **dbt**
3. Configure:
   ```yaml
   Name: cascade-dbt
   dbt Manifest Path: /dbt/target/manifest.json
   dbt Catalog Path: /dbt/target/catalog.json
   ```

## Advanced Features

### Quality Checks

Add data quality tests in OpenMetadata UI:

1. Navigate to table
2. Click **Profiler & Data Quality**
3. Add tests:
   - Column null checks
   - Value range validations
   - Uniqueness constraints

### Glossary Terms

Create a business glossary:

1. **Settings** → **Glossary**
2. Add terms:
   - **Time in Range (TIR)**: Percentage of glucose readings within target range (70-180 mg/dL)
   - **A1C**: Hemoglobin A1C estimated from mean glucose
3. Link terms to table columns

### API Access

OpenMetadata provides a REST API:

```bash
# Get all tables
curl http://localhost:10020/api/v1/tables

# Get specific table
curl http://localhost:10020/api/v1/tables/name/iceberg.silver.glucose_daily_stats

# Search
curl "http://localhost:10020/api/v1/search/query?q=glucose"
```

## Integration with Cascade Workflows

### Update Ingestion Schedule

Match OpenMetadata ingestion with your Dagster pipelines:

```yaml
Dagster Pipeline: Daily at 2:00 AM
OpenMetadata Ingestion: Daily at 3:00 AM (1 hour after data refresh)
```

### Document in dbt Models

Add descriptions to dbt models that will appear in OpenMetadata:

```yaml
# transforms/dbt/models/silver/glucose_daily_stats.yml
version: 2

models:
  - name: glucose_daily_stats
    description: |
      Daily aggregated glucose statistics with A1C estimates.
      Source: bronze.entries_cleaned
      Refresh: Daily at 2 AM
    columns:
      - name: date
        description: Measurement date (partition key)
      - name: mean_glucose
        description: Daily average glucose in mg/dL
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 40
              max_value: 400
```

## Troubleshooting

### OpenMetadata UI Not Loading

```bash
# Check service health
make health-catalog

# Check logs
docker logs openmetadata-server
docker logs openmetadata-mysql
docker logs openmetadata-elasticsearch
```

### Elasticsearch Out of Memory

If you see OOM errors, increase memory:

```yaml
# In docker-compose.yml
openmetadata-elasticsearch:
  environment:
    ES_JAVA_OPTS: "-Xms1g -Xmx1g"  # Increase from 512m
```

### Trino Connection Failed

Ensure Trino is running:

```bash
make health

# Start Trino if not running
make up-query
```

Check connection from OpenMetadata container:

```bash
docker exec -it openmetadata-server curl http://trino:8080/v1/info
```

### Ingestion Pipeline Failing

1. Check logs in OpenMetadata UI → **Settings** → **Services** → **Ingestion Logs**
2. Verify schemas exist in Trino:
   ```bash
   make trino-shell
   SHOW SCHEMAS FROM iceberg;
   ```

## Resource Requirements

**Minimum:**
- 6 GB RAM
- 4 vCPUs
- 10 GB disk space

**Recommended:**
- 8 GB RAM
- 6 vCPUs
- 20 GB disk space

## Best Practices

1. **Document Everything**: Add descriptions to all tables and columns
2. **Use Tags**: Create a consistent tagging strategy (layers, domains, sensitivity)
3. **Set Ownership**: Assign owners to all datasets
4. **Regular Updates**: Run ingestion daily to keep metadata fresh
5. **Quality Checks**: Add data quality tests to critical tables
6. **Glossary**: Maintain business terms for domain-specific language

## Comparison with Alternatives

| Feature | OpenMetadata | Amundsen | DataHub |
|---------|--------------|----------|---------|
| Setup Ease | ⭐⭐ Moderate | ⭐ Easy | ⭐⭐⭐ Complex |
| Active Development | ✅ Active | ⚠️ Slowed | ✅ Very Active |
| UI/UX | Excellent | Good | Very Good |
| Resource Usage | Medium (6GB) | Low | High (Kafka) |
| Iceberg Support | ✅ Yes | ❌ No | ✅ Yes |

## Next Steps

1. **Enrich Metadata**: Add descriptions and tags to all tables
2. **Set Up dbt Ingestion**: Enable lineage tracking from dbt models
3. **Create Glossary**: Define business terms
4. **Add Quality Tests**: Monitor data quality
5. **Enable Alerts**: Get notified about schema changes

## Additional Resources

- [OpenMetadata Documentation](https://docs.open-metadata.org/)
- [Trino Connector Guide](https://docs.open-metadata.org/connectors/database/trino)
- [Data Quality Guide](https://docs.open-metadata.org/how-to-guides/data-quality-observability)
- [API Documentation](https://docs.open-metadata.org/developers/apis)

## Related Cascade Documentation

- [Quick Start Guide](quick-start.md) - Get Cascade running
- [API Documentation](API.md) - FastAPI and Hasura setup
- [DBT Development Guide](DBT_DEVELOPMENT_GUIDE.md) - Creating dbt models
- [Workflow Development Guide](WORKFLOW_DEVELOPMENT_GUIDE.md) - Dagster pipelines
