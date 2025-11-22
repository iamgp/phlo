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

### 3. Complete Setup Checklist

After first-time setup, you MUST complete these steps in order:

1. ✅ Configure Trino data source (see "Setting Up Trino Source" section)
2. ✅ Create and run metadata ingestion pipeline
3. ✅ **Enable search indices** (Settings → OpenMetadata → Search → Run with "Recreate Indexes")
4. ✅ Verify search works on Explore page

**Skip step 3 at your own peril** - without it, search and the Explore page will be completely broken.

### 3. First Login

1. Navigate to http://localhost:10020
2. Login with `admin` / `admin`
3. Complete the welcome tour (optional)
4. You'll see the empty catalog dashboard

## Connecting Cascade Data Sources

### Step 1: Add Trino Database Service

1. Click **Settings** (gear icon) in the top-right corner
2. Navigate to **Integrations** → **Databases**
3. Click **Add New Service**
4. Select **Trino** from the list of database types
5. Click **Next**

### Step 2: Configure Trino Connection

**Service Name:**
```
trino
```

**Description (optional):**
```
Cascade lakehouse Trino query engine with Iceberg catalog
```

**Connection Configuration:**

Click on **Basic** authentication type, then configure:

| Field | Value | Notes |
|-------|-------|-------|
| **Host** | `trino` | Docker service name (internal network) |
| **Port** | `8080` | Internal container port (NOT 10005!) |
| **Username** | `cascade` | Any username (no auth in dev) |
| **Catalog** | Leave empty | We'll filter by catalog in ingestion |
| **Database Schema** | Leave empty | - |

> **Port Note:** Trino runs on port `8080` inside the Docker network. The external host port `10005` is only for accessing Trino from your laptop. OpenMetadata uses the internal port `8080`.

**Advanced Options (leave defaults):**
- Connection Options: (empty)
- Connection Arguments: (empty)

Click **Test Connection** - you should see:
```
Connection test was successful
```

If the test fails, verify Trino is running:
```bash
docker ps --filter name=trino
curl http://localhost:8080/v1/info
```

Click **Submit** to save the service.

### Step 3: Configure Metadata Ingestion Pipeline

After creating the service, you'll be prompted to set up metadata ingestion.

1. **Pipeline Name:** `trino-metadata`
2. **Pipeline Type:** Select **Metadata Ingestion**
3. Click **Next**

**Metadata Configuration:**

**Filter Patterns (CRITICAL - prevents crashes):**

```yaml
Database Filter Pattern:
  Include: iceberg
  Exclude: system

Schema Filter Pattern:
  Include: raw, bronze, silver, gold
  Exclude: information_schema

Table Filter Pattern:
  Include: .*
  Exclude: (leave empty)
```

**Advanced Configuration:**

Enable/disable these options:

| Option | Enable? | Reason |
|--------|---------|--------|
| Include Tables | ✅ Yes | Core metadata |
| Include Views | ✅ Yes | Include views |
| Include Tags | ✅ Yes | Catalog tags |
| Include Owners | ❌ No | Not used in dev |
| Include Stored Procedures | ❌ **NO** | **Causes crashes** |
| Mark Deleted Stored Procedures | ❌ **NO** | **Causes crashes** |
| Include DDL | ❌ No | Not needed |
| Override Metadata | ❌ No | - |

**Ingestion Settings:**
- Thread Count: `1` (default)
- Timeout: `300` seconds (default)

**Query Log Ingestion:** Skip for now (can add later for lineage)

Click **Next**.

### Step 4: Configure Scheduling

**Schedule Type:** Choose one:

**Option A: Manual (Recommended for Development)**
- Select **Manual**
- Run ingestion on-demand when you need to refresh metadata
- Good for: Development, testing

**Option B: Scheduled (Recommended for Production)**
- Select **Scheduled**
- Choose **Cron Expression**
- Enter: `0 3 * * *` (runs daily at 3 AM, after Dagster pipelines complete)
- Timezone: `UTC`

Click **Next**.

### Step 5: Review and Deploy

1. Review your configuration
2. Click **Deploy**
3. The pipeline will be created and registered with Airflow

You'll see a success message with the pipeline ID.

### Step 6: Run Initial Ingestion

**Via OpenMetadata UI:**

1. Go to **Settings → Integrations → Databases**
2. Click on **trino** service
3. Click **Ingestions** tab
4. Find `trino-metadata` pipeline
5. Click **Run** (play button)
6. Monitor progress in real-time

**Via Airflow UI (Alternative):**

1. Open http://localhost:8080/
2. Login with `admin` / `admin`
3. Find DAG named `trino_metadata_<id>` or similar
4. Toggle it **ON** (unpause the DAG)
5. Click **Trigger DAG** (play button)
6. Click on the DAG run to view logs

**Expected Output:**

```
INFO - Starting metadata ingestion
INFO - Connecting to Trino at trino:8080
INFO - Processing catalog: iceberg
INFO - Processing schema: raw
INFO - Discovered 1 tables in schema raw
INFO - Processing table: glucose_entries
INFO - Successfully ingested table: trino.iceberg.raw.glucose_entries
INFO - Processing schema: bronze
INFO - Processing schema: silver
INFO - Processing schema: gold
INFO - Metadata ingestion completed
INFO - Total tables ingested: 15
INFO - Total schemas ingested: 4
INFO - Total errors: 0
```

### Step 7: Enable Search (CRITICAL)

After initial ingestion, search will NOT work until you populate the search index. This is a required step.

**Navigate to Search Settings:**

1. Go to **Settings** (gear icon) → **OpenMetadata** → **Search**
2. Click on **SearchIndexingApplication**
3. Click **Run Now** button

**Configure the Reindex Job:**

1. Enable **"Recreate Indexes"** toggle (IMPORTANT)
2. Select **"All"** entities (or leave default)
3. Click **Submit**

**Monitor Progress:**

- The job will run for 1-2 minutes
- You'll see "Success" when complete
- Or check logs:
  ```bash
  docker logs openmetadata-server --tail 100 | grep -i "reindex"
  ```

**What This Does:**

- Creates the `all` search alias
- Populates search indices from metadata
- Enables Explore page and search functionality

**Without this step:**
- Explore page will show error: "Search failed due to Elasticsearch exception"
- Global search will not work
- You can only navigate by direct URLs

### Step 8: Verify Everything Works

**Check Search Works:**

1. Go to **Explore** page
2. Should see databases/tables listed (no errors)
3. Type `glucose` in search bar
4. Should find `glucose_entries` table

**Browse via Navigation:**

1. Go to **Settings → Services → Database Services**
2. Click on **trino**
3. Navigate: iceberg → raw → glucose_entries
4. You should see:
   - Table schema with all columns
   - Column descriptions
   - Sample data (if profiling enabled)

**Direct URL Access:**
```
http://localhost:10020/table/trino.iceberg.raw.glucose_entries
```

**Verify in Airflow:**
```bash
docker logs openmetadata-ingestion | grep "Successfully ingested"
```

**Check Elasticsearch Indices:**
```bash
# Verify tables are indexed
docker exec openmetadata-elasticsearch curl -s \
  "http://localhost:9200/table_search_index/_count"

# Should show: {"count": 6, ...}
```

## Configuration Reference

### Complete Ingestion Configuration

This is what your pipeline configuration looks like (stored in `volumes/openmetadata-ingestion-dags/<pipeline-id>.json`):

```json
{
  "source": {
    "type": "trino",
    "serviceName": "trino",
    "sourceConfig": {
      "config": {
        "type": "DatabaseMetadata",
        "markDeletedTables": true,
        "markDeletedStoredProcedures": false,
        "includeTables": true,
        "includeViews": true,
        "includeTags": true,
        "includeOwners": false,
        "includeStoredProcedures": false,
        "includeDDL": false,
        "overrideMetadata": false,
        "databaseFilterPattern": {
          "includes": ["iceberg"],
          "excludes": ["system"]
        },
        "schemaFilterPattern": {
          "includes": ["raw", "bronze", "silver", "gold"],
          "excludes": ["information_schema"]
        },
        "tableFilterPattern": {
          "includes": [".*"]
        },
        "threads": 1,
        "queryLogDuration": 1
      }
    }
  },
  "sink": {
    "type": "metadata-rest",
    "config": {}
  },
  "workflowConfig": {
    "loggerLevel": "INFO",
    "openMetadataServerConfig": {
      "hostPort": "http://openmetadata-server:8585/api",
      "authProvider": "openmetadata",
      "securityConfig": {
        "jwtToken": "<auto-generated>"
      }
    }
  },
  "airflowConfig": {
    "pausePipeline": false,
    "concurrency": 1,
    "pipelineCatchup": false,
    "pipelineTimezone": "UTC",
    "retries": 0,
    "retryDelay": 300,
    "maxActiveRuns": 1
  }
}
```

### Editing Configuration Later

**Via UI:**
1. Go to **Settings → Databases → trino**
2. Click **Ingestions** tab
3. Click **Edit** (pencil icon) on your pipeline
4. Modify configuration
5. Click **Save**
6. Re-run the pipeline

**Via File (Advanced):**
```bash
# Find your pipeline configuration
ls volumes/openmetadata-ingestion-dags/

# Edit the JSON file directly
vim volumes/openmetadata-ingestion-dags/<pipeline-id>.json

# Restart Airflow to pick up changes
docker restart openmetadata-ingestion
```

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

### Enable Lineage Tracking with dbt

Lineage is automatically extracted from:
- **dbt models** - Shows dependencies between models and tables
- **SQL queries** - Enable query log ingestion (advanced)

**Step 1: Add dbt Service**

1. Go to **Settings** → **Services** → **Pipeline Services**
2. Click **Add Service**
3. Select **dbt**
4. Configure:

| Field | Value |
|-------|-------|
| **Name** | `cascade-dbt` |
| **dbt Cloud API URL** | Leave empty (we use local files) |
| **dbt Cloud Account ID** | Leave empty |

Click **Next**.

**Step 2: Configure dbt Metadata Ingestion**

1. **Source Configuration:**

| Field | Value | Notes |
|-------|-------|-------|
| **dbt Configuration Source** | `Local` | We're using local files, not dbt Cloud |
| **dbt Catalog File Path** | `/dbt/target/catalog.json` | Contains column-level metadata |
| **dbt Manifest File Path** | `/dbt/target/manifest.json` | Contains lineage and dependencies |
| **dbt Run Results File Path** | `/dbt/target/run_results.json` | Optional: test results |

2. **Database Service Name:** `trino`
   - This links dbt models to your Trino tables
   - Must match the name of your Trino service

3. **Include Tags:** `Yes` (Enable)
   - Imports dbt model tags as OpenMetadata tags

Click **Next**.

**Step 3: Schedule dbt Ingestion**

**For Development:**
- Select **Manual**
- Run after `dbt run` or `dbt build` completes

**For Production:**
- Select **Scheduled**
- Cron: `0 4 * * *` (4 AM, after Dagster + Trino ingestion)

Click **Next** → **Deploy**.

**Step 4: Run dbt Ingestion**

1. Ensure dbt artifacts are fresh:
   ```bash
   # From your local machine
   cd transforms/dbt
   dbt compile --profiles-dir ./profiles

   # Or run the full build
   dbt build --profiles-dir ./profiles
   ```

2. Go to **Settings → Integrations → Pipeline → cascade-dbt**
3. Click **Ingestions** tab
4. Find `cascade-dbt-metadata` pipeline
5. Click **Run** (play button)

**Expected Output:**
```
INFO - Starting dbt metadata ingestion
INFO - Reading manifest from /dbt/target/manifest.json
INFO - Found 12 dbt models
INFO - Processing model: glucose_daily_stats
INFO - Linking model to table: trino.iceberg.silver.glucose_daily_stats
INFO - Extracted lineage: bronze.entries_cleaned → silver.glucose_daily_stats
INFO - Successfully ingested dbt metadata
```

**What You'll See:**

After ingestion:
1. **Enhanced Table Descriptions**: dbt model descriptions appear on tables
2. **Column Descriptions**: From dbt schema YAML files
3. **Lineage Graphs**: Visual connections between models
4. **dbt Tags**: As OpenMetadata tags on tables
5. **Test Results**: dbt tests show as data quality metrics

**Verify dbt Integration:**

Navigate to a table created by dbt (e.g., `silver.glucose_daily_stats`):
- **Lineage** tab: Shows upstream dependencies
- **Schema** tab: Has column descriptions from dbt
- **Data Quality** tab: Shows dbt test results

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

**Common causes:**
1. Database migrations haven't run yet
2. Server still initializing (wait 2-3 minutes)
3. Dependency services not healthy

**Check migration status:**
```bash
# Verify migration completed successfully
docker logs openmetadata-migrate

# Check exit code (should be 0)
docker inspect openmetadata-migrate --format='{{.State.ExitCode}}'
```

### Search Not Working / "All Shards Failed" Error

**Symptom:**
- Explore page shows: "Search failed due to Elasticsearch exception [type=search_phase_execution_exception, reason=all shards failed]"
- Global search returns no results
- Direct table URLs work fine

**Cause:** The `all` search index is not populated after initial setup.

**Solution:**

1. Go to **Settings → OpenMetadata → Search**
2. Click on **SearchIndexingApplication**
3. Click **Run Now**
4. **IMPORTANT:** Enable "Recreate Indexes" toggle
5. Click **Submit**
6. Wait 1-2 minutes for completion
7. Refresh browser and test search

**If reindex fails with "Invalid alias name [all]" error:**

```bash
# Delete the incorrect index
docker exec openmetadata-elasticsearch curl -s -X DELETE "http://localhost:9200/all"

# Run reindex again from UI with "Recreate Indexes" enabled
```

**Verify search is working:**
```bash
# Check all alias exists and points to indices
docker exec openmetadata-elasticsearch curl -s "http://localhost:9200/_cat/aliases?v" | grep all

# Test search query
docker exec openmetadata-elasticsearch curl -s \
  "http://localhost:9200/all/_search?q=glucose&size=1" | grep -o '"total":{"value":[0-9]*'
```

### Airflow Authentication Failed

**Error:** `Authentication failed for user [admin] trying to access the Airflow APIs`

This occurs when connecting ingestion pipelines after a fresh install.

**Solution:**
```bash
# Reset Airflow admin password
docker exec openmetadata-ingestion airflow users reset-password -u admin -p admin

# Restart Airflow
docker restart openmetadata-ingestion
```

### Missing Elasticsearch Indices

**Error:** `Failed to find index table_search_index` or similar

**Root cause:** OpenMetadata should create Elasticsearch indices automatically on startup. If you see this error, it indicates the initialization failed.

**Verification:**
```bash
# Check if indices exist
docker exec openmetadata-elasticsearch curl -s http://localhost:9200/_cat/indices | grep search_index
```

**Solution:**
Indices should be created automatically by OpenMetadata. If they're missing after a fresh install:

1. Check OpenMetadata server logs for initialization errors:
   ```bash
   docker logs openmetadata-server | grep -i "elastic\|index"
   ```

2. Restart OpenMetadata server to trigger re-initialization:
   ```bash
   docker restart openmetadata-server
   ```

3. If problem persists, this is a bug in OpenMetadata 1.6.1 - report to the OpenMetadata team

### Server Crashes During Ingestion

**Symptoms:**
- OpenMetadata server keeps restarting
- Container shows "Restarting (137)" or "Killed"
- Logs show signal 9 or OOM errors

**Root cause:** Memory exhaustion, typically from stored procedure queries

**Solution:**

1. **Disable stored procedures** in ingestion configuration:
   - Edit your Trino service ingestion pipeline
   - Advanced Options → Uncheck "Include Stored Procedures"
   - Advanced Options → Uncheck "Mark Deleted Stored Procedures"

2. **Add schema filters** to reduce scope:
   ```yaml
   Include Schemas: raw,bronze,silver,gold
   Exclude Schemas: information_schema,system
   Include Databases: iceberg
   ```

3. **Increase server memory** if crashes continue:
   ```yaml
   # In docker-compose.yml
   openmetadata-server:
     environment:
       OPENMETADATA_HEAP_OPTS: "-Xmx4G -Xms4G"  # Increase from default
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
3. Check Airflow DAG execution:
   - Access Airflow at http://localhost:8080/
   - Login: `admin` / `admin`
   - View DAG logs for detailed error messages

### Tables Not Appearing After Ingestion

**Problem:** Ingestion runs successfully but tables don't show in UI

**Solutions:**

1. **Check if ingestion actually found tables:**
   ```bash
   docker logs openmetadata-ingestion | grep "Successfully ingested"
   ```

2. **Verify schema filters aren't too restrictive:**
   - Go to Settings → Database Services → trino → Ingestion
   - Check Include/Exclude Schemas configuration
   - Ensure your target schemas are included

3. **Search by fully qualified name:**
   - In UI search bar: `trino.iceberg.raw.glucose_entries`
   - Navigate to Explore → Tables and browse database hierarchy

4. **Check Elasticsearch index:**
   ```bash
   # Verify table is in Elasticsearch
   docker exec openmetadata-elasticsearch curl -s \
     "http://localhost:9200/table_search_index/_search?q=glucose_entries&pretty"
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
- [API Documentation](../reference/api.md) - FastAPI and Hasura setup
- [dbt Development Guide](../guides/dbt-development.md) - Creating dbt models
- [Workflow Development Guide](../guides/workflow-development.md) - Dagster pipelines
