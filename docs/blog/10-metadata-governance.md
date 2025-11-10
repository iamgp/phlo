# Part 10: Metadata and Governance with OpenMetadata

Data quality is important. But knowing what you have, where it came from, and who can use it is equally critical. This post covers metadata and governance with OpenMetadata.

## The Metadata Problem

Without metadata tracking:

```
Tuesday 3pm: Someone asks "Where did this dataset come from?"

Answers from your team:
- Engineer 1: "I think Nightscout API?"
- Engineer 2: "Maybe it's in the glucose_readings table"
- Data analyst: "I don't know, it's in the dashboard"
- Manager: "How many people depend on this?"
```

Nobody knows because metadata is scattered:

- Table definitions in dbt YAML
- Column notes in dbt docs
- Data source info in Dagster assets
- Lineage unclear
- Ownership unknown
- Change history nowhere

## OpenMetadata: The Open-Source Data Catalog

OpenMetadata is an open-source data catalog that answers:

- What data exists?
- Where is it stored?
- How is it related?
- Who owns it?
- What does it mean?
- How often is it updated?
- What quality checks does it have?

## Why OpenMetadata for Cascade?

OpenMetadata integrates seamlessly with Cascade's tech stack:

- **Trino connector** - Auto-discovers Iceberg tables
- **Modern UI** - Intuitive search and browsing experience
- **Active development** - Regular updates and improvements
- **Simple architecture** - MySQL + Elasticsearch (6GB RAM required)
- **Open source** - No licensing costs

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
┌──────▼──────────────────────────┐
│  Trino → Iceberg Tables (Nessie)│
│  - raw.glucose_entries           │
│  - bronze.stg_glucose_entries    │
│  - silver.fct_glucose_readings   │
│  - gold.dim_date                 │
└──────────────────────────────────┘
```

## Quick Start with OpenMetadata

### 1. Start OpenMetadata Services

```bash
# Start the data catalog stack
make up-catalog

# Check health status
make health-catalog
```

Expected output:
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

Default credentials:
- Username: `admin`
- Password: `admin`

> Security Note: Change the default password in production by updating `OPENMETADATA_ADMIN_PASSWORD` in `.env`

## Setting Up Trino Data Source

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

**Description:**
```
Cascade lakehouse Trino query engine with Iceberg catalog
```

**Connection Configuration:**

Click on **Basic** authentication type, then configure:

| Field | Value | Notes |
|-------|-------|-------|
| **Host** | `trino` | Docker service name (internal network) |
| **Port** | `8080` | Internal container port |
| **Username** | `cascade` | Any username (no auth in dev) |
| **Catalog** | Leave empty | We'll filter by catalog in ingestion |
| **Database Schema** | Leave empty | - |

> Port Note: Trino runs on port `8080` inside the Docker network. The external host port `10005` is only for accessing Trino from your laptop. OpenMetadata uses the internal port `8080`.

Click **Test Connection** - you should see:
```
Connection test was successful
```

Click **Submit** to save the service.

### Step 3: Configure Metadata Ingestion Pipeline

After creating the service, you'll be prompted to set up metadata ingestion.

1. **Pipeline Name:** `trino-metadata`
2. **Pipeline Type:** Select **Metadata Ingestion**
3. Click **Next**

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
| Include Tables | Yes | Core metadata |
| Include Views | Yes | Include views |
| Include Tags | Yes | Catalog tags |
| Include Owners | No | Not used in dev |
| Include Stored Procedures | **NO** | **Causes crashes** |
| Mark Deleted Stored Procedures | **NO** | **Causes crashes** |
| Include DDL | No | Not needed |
| Override Metadata | No | - |

**Ingestion Settings:**
- Thread Count: `1` (default)
- Timeout: `300` seconds (default)

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

Click **Next** → **Deploy**.

### Step 5: Run Initial Ingestion

**Via OpenMetadata UI:**

1. Go to **Settings → Integrations → Databases**
2. Click on **trino** service
3. Click **Ingestions** tab
4. Find `trino-metadata` pipeline
5. Click **Run** (play button)
6. Monitor progress in real-time

Expected output:
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

### Step 6: Enable Search (CRITICAL)

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

**What This Does:**

- Creates the `all` search alias
- Populates search indices from metadata
- Enables Explore page and search functionality

**Without this step:**
- Explore page will show error: "Search failed due to Elasticsearch exception"
- Global search will not work
- You can only navigate by direct URLs

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

1. Click on a table (e.g., `silver.fct_glucose_readings`)
2. Click **Edit** (pencil icon)
3. Add description:

```markdown
## Description
Fact table of glucose readings with calculated categories and metrics.

## Update Schedule
Updated every 5 minutes via Dagster pipeline.

## Business Logic
- `glucose_category`: Categorized as hypoglycemia (<70), in_range (70-180), or hyperglycemia (>180)
- `reading_timestamp`: UTC timestamp of the reading
```

4. Add column descriptions:
   - `reading_id`: Unique identifier for each glucose reading
   - `glucose_mg_dl`: Glucose value in mg/dL (validated range: 20-600)
   - `glucose_category`: Categorized glucose level
   - `reading_timestamp`: When the reading was taken (UTC)

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
raw.glucose_entries
    ↓
bronze.stg_glucose_entries (dbt model)
    ↓
silver.fct_glucose_readings (dbt model)
    ↓
gold.dim_date (dbt model)
    ↓
marts.mrt_glucose_overview (Trino publish)
```

### Enable Lineage Tracking with dbt

Lineage is automatically extracted from:
- **dbt models** - Shows dependencies between models and tables
- **SQL queries** - Enable query log ingestion (advanced)

**Step 1: Add dbt Service**

1. Go to **Settings → Services → Pipeline Services**
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
   cd transforms/dbt
   dbt compile --profiles-dir ./profiles
   ```

2. Go to **Settings → Integrations → Pipeline → cascade-dbt**
3. Click **Ingestions** tab
4. Find `cascade-dbt-metadata` pipeline
5. Click **Run** (play button)

Expected output:
```
INFO - Starting dbt metadata ingestion
INFO - Reading manifest from /dbt/target/manifest.json
INFO - Found 12 dbt models
INFO - Processing model: fct_glucose_readings
INFO - Linking model to table: trino.iceberg.silver.fct_glucose_readings
INFO - Extracted lineage: bronze.stg_glucose_entries → silver.fct_glucose_readings
INFO - Successfully ingested dbt metadata
```

## Governance Workflows

### 1. Impact Analysis

Question: "Can I delete the `raw.glucose_entries` table?"

OpenMetadata shows:
```
raw.glucose_entries
├─ Downstream: bronze.stg_glucose_entries
│  ├─ Downstream: silver.fct_glucose_readings
│  │  ├─ Downstream: gold.mrt_glucose_overview
│  │  │  └─ Used by: Dashboard "Glucose Monitoring"
│  │  └─ Used by: 3 dbt models
│  └─ Used by: 2 dbt models
│
└─ Owner: data-platform-team

Answer: NO!
  It impacts:
  - 3 downstream datasets
  - 1 dashboard
  - Multiple dbt models
```

### 2. Search and Discovery

```
OpenMetadata Search: "glucose"

Results:
────────
1. fct_glucose_readings (Dataset)
   Silver layer • Iceberg • 487K rows
   "Glucose readings fact table"
   Owner: data-platform-team

2. stg_glucose_entries (Dataset)
   Bronze layer • Iceberg • 500K rows
   "Staged glucose entries"

3. mrt_glucose_overview (Dataset)
   Gold layer • Postgres marts • 5K rows
   "Marketing-ready glucose metrics"
```

### 3. Data Access Governance

Track who has access to what:

1. Navigate to table
2. View **Activity Feeds**
3. See who accessed, queried, or modified

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
# transforms/dbt/models/silver/fct_glucose_readings.yml
version: 2

models:
  - name: fct_glucose_readings
    description: |
      Fact table of glucose readings with calculated categories.
      Source: bronze.stg_glucose_entries
      Refresh: Every 5 minutes
    columns:
      - name: reading_id
        description: Unique identifier
      - name: glucose_mg_dl
        description: Glucose value in mg/dL (validated 20-600)
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 20
              max_value: 600
      - name: glucose_category
        description: Categorized as hypoglycemia, in_range, or hyperglycemia
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

### Search Not Working

**Symptom:**
- Explore page shows: "Search failed due to Elasticsearch exception"
- Global search returns no results

**Solution:**

1. Go to **Settings → OpenMetadata → Search**
2. Click on **SearchIndexingApplication**
3. Click **Run Now**
4. **IMPORTANT:** Enable "Recreate Indexes" toggle
5. Click **Submit**
6. Wait 1-2 minutes for completion

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

## Best Practices

1. **Document Everything**: Add descriptions to all tables and columns
2. **Use Tags**: Create a consistent tagging strategy (layers, domains, sensitivity)
3. **Set Ownership**: Assign owners to all datasets
4. **Regular Updates**: Run ingestion daily to keep metadata fresh
5. **Quality Checks**: Link data quality tests to tables
6. **Glossary**: Maintain business terms for domain-specific language

## Benefits of Metadata Management

**Self-Service**: New analysts discover datasets without asking
**Compliance**: Track who accessed what, when, and why
**Impact Analysis**: Understand dependencies before changes
**Accountability**: Clear ownership and change history
**Quality**: Quality checks visible and tracked
**Documentation**: Single source of truth for data definitions

## Summary

OpenMetadata provides:

1. **Catalog**: Discover all datasets with descriptions
2. **Lineage**: Understand data flow end-to-end
3. **Governance**: Track ownership and access
4. **Quality**: Link validation checks to datasets
5. **History**: Change tracking and audit trail
6. **Impact**: See what breaks when data changes

Integrated with dbt, Dagster, and Iceberg, OpenMetadata becomes your data OS.

**Next**: [Part 11: Observability and Monitoring](11-observability-monitoring.md)

See you there!
