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

> **Note:** For detailed OpenMetadata setup instructions, see [docs/setup/openmetadata.md](/home/user/phlo/docs/setup/openmetadata.md)

## OpenMetadata: The Open-Source Data Catalog

OpenMetadata is an open-source data catalog that answers:

- What data exists?
- Where is it stored?
- How is it related?
- Who owns it?
- What does it mean?
- How often is it updated?
- What quality checks does it have?

## Why OpenMetadata for Phlo?

OpenMetadata integrates seamlessly with Phlo's tech stack:

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

> Security Note: Change the default password in production by updating `OPENMETADATA_ADMIN_PASSWORD` in `.phlo/.env.local`

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
Phlo lakehouse Trino query engine with Iceberg catalog
```

**Connection Configuration:**

Click on **Basic** authentication type, then configure:

| Field               | Value       | Notes                                  |
| ------------------- | ----------- | -------------------------------------- |
| **Host**            | `trino`     | Docker service name (internal network) |
| **Port**            | `8080`      | Internal container port                |
| **Username**        | `phlo`      | Any username (no auth in dev)          |
| **Catalog**         | Leave empty | We'll filter by catalog in ingestion   |
| **Database Schema** | Leave empty | -                                      |

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

| Option                         | Enable? | Reason             |
| ------------------------------ | ------- | ------------------ |
| Include Tables                 | Yes     | Core metadata      |
| Include Views                  | Yes     | Include views      |
| Include Tags                   | Yes     | Catalog tags       |
| Include Owners                 | No      | Not used in dev    |
| Include Stored Procedures      | **NO**  | **Causes crashes** |
| Mark Deleted Stored Procedures | **NO**  | **Causes crashes** |
| Include DDL                    | No      | Not needed         |
| Override Metadata              | No      | -                  |

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

| Field                    | Value                            |
| ------------------------ | -------------------------------- |
| **Name**                 | `phlo-dbt`                       |
| **dbt Cloud API URL**    | Leave empty (we use local files) |
| **dbt Cloud Account ID** | Leave empty                      |

Click **Next**.

**Step 2: Configure dbt Metadata Ingestion**

1. **Source Configuration:**

| Field                         | Value                          | Notes                                  |
| ----------------------------- | ------------------------------ | -------------------------------------- |
| **dbt Configuration Source**  | `Local`                        | We're using local files, not dbt Cloud |
| **dbt Catalog File Path**     | `/dbt/target/catalog.json`     | Contains column-level metadata         |
| **dbt Manifest File Path**    | `/dbt/target/manifest.json`    | Contains lineage and dependencies      |
| **dbt Run Results File Path** | `/dbt/target/run_results.json` | Optional: test results                 |

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
   cd workflows/transforms/dbt
   dbt compile --profiles-dir ./profiles
   ```

2. Go to **Settings → Integrations → Pipeline → phlo-dbt**
3. Click **Ingestions** tab
4. Find `phlo-dbt-metadata` pipeline
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

You can use the `phlo lineage impact` command (see Part 11) or check OpenMetadata:

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

## Integration with Phlo Workflows

### Update Ingestion Schedule

Match OpenMetadata ingestion with your Dagster pipelines:

```yaml
Dagster Pipeline: Daily at 2:00 AM
OpenMetadata Ingestion: Daily at 3:00 AM (1 hour after data refresh)
```

### Document in dbt Models

Add descriptions to dbt models that will appear in OpenMetadata:

```yaml
# workflows/transforms/dbt/models/silver/fct_glucose_readings.yml
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

## Data Contracts: Formalizing Data Agreements

As data platforms grow, informal agreements break down. The ML team assumes glucose readings update hourly. The analytics team expects certain columns to never be null. The reporting system depends on specific value ranges. When someone changes the schema or update frequency, things break.

**Data contracts** formalize these agreements between data producers (your pipelines) and data consumers (dashboards, ML models, downstream teams).

### The Problem Contracts Solve

```
Without contracts:

Monday:    Engineer adds new column, removes old one
Tuesday:   ML model training fails silently
Wednesday: Dashboard shows "No Data"
Thursday:  Analyst reports: "Numbers look wrong"
Friday:    Fire drill to understand what changed and why
```

With contracts, breaking changes are caught before deployment.

### Anatomy of a Data Contract

Contracts live in your `contracts/` directory as YAML files. Here's a real example from the glucose platform:

```yaml
# phlo-examples/nightscout/contracts/glucose_readings.yaml
name: glucose_readings
version: 1.0.0
owner: data-team
description: "Contract for glucose readings from Nightscout API"

schema:
  required_columns:
    - name: reading_id
      type: string
      description: "Unique identifier for each glucose reading"
      constraints:
        unique: true
        nullable: false

    - name: sgv
      type: integer
      description: "Sensor glucose value in mg/dL"
      constraints:
        min: 20
        max: 600
        nullable: false

    - name: reading_timestamp
      type: timestamp
      description: "When the reading was taken (UTC)"
      constraints:
        nullable: false

sla:
  freshness_hours: 2 # Data must be < 2 hours old
  quality_threshold: 0.99 # 99% of rows must pass validation
  availability_percentage: 99.9

consumers:
  - name: analytics-team
    usage: "BI dashboards and ad-hoc analysis"
    contact: "analytics@example.com"

  - name: ml-team
    usage: "Model training and feature engineering"
    contact: "ml@example.com"

notifications:
  channels:
    - type: slack
      channel: "#data-alerts"
  on_events:
    - schema_change_proposed
    - sla_breach
    - quality_violation
```

### How Contract Validation Works

When you run `phlo contract validate glucose_readings`, Phlo:

1. **Loads the contract** from `contracts/glucose_readings.yaml` (or `phlo-examples/nightscout/contracts/glucose_readings.yaml` for examples)
2. **Validates** the contract schema and structure
3. **Reports** expected schema and SLA requirements

> **Note:** Full table schema comparison against live Iceberg tables is planned for a future release. Currently, the command validates contract syntax and displays expected requirements.

```bash
$ phlo contract validate glucose_readings

Contract Validation: glucose_readings

Note: Requires live catalog access to validate actual schema

Required Columns:
  reading_id   string
  sgv          integer
  reading_timestamp timestamp
  direction    string
  device       string
```

To check for contract violations against actual tables, you would use:

```bash
$ phlo contract show glucose_readings  # View full contract details
$ phlo catalog describe raw.glucose_entries  # View actual table schema
```

### Schema Evolution and Breaking Changes

The real power of contracts is **preventing breaking changes**. When you modify a schema, Phlo classifies changes:

| Change Type               | Classification | Action          |
| ------------------------- | -------------- | --------------- |
| Add nullable column       | SAFE           | Auto-approve    |
| Add column with default   | SAFE           | Auto-approve    |
| Change column description | WARNING        | Review required |
| Add new constraint        | WARNING        | Review required |
| Remove column             | BREAKING       | Block merge     |
| Change column type        | BREAKING       | Block merge     |
| Remove nullable           | BREAKING       | Block merge     |

In CI/CD, run `phlo contract check --pr` to validate changes before merge:

```bash
$ phlo contract check --pr

Checking contracts against PR changes...

glucose_readings:
  BREAKING: Column 'device_type' removed

  Impact:
    - analytics-team: BI dashboards (contact: analytics@example.com)
    - ml-team: Model training (contact: ml@example.com)

  Action Required:
    1. Notify consumers before removing column
    2. Add deprecation period (recommended: 30 days)
    3. Get explicit approval from consumers
    4. Use --force to override (not recommended)

Contract check FAILED - 1 breaking change detected
```

### Consumer Notifications

When contracts change, affected teams get notified automatically:

```
#data-alerts Slack Channel:

🔔 Schema Change Proposed: glucose_readings

Changes:
  • Column 'legacy_id' marked for removal
  • New column 'device_model' added (nullable)

Affected Consumers:
  • analytics-team (BI dashboards)
  • ml-team (Model training)

PR: https://github.com/org/repo/pull/123
Review by: Friday 5pm

React with ✅ to approve or 🚫 to block
```

---

## Schema Management via CLI

Beyond contracts, Phlo provides tools for managing Pandera schemas themselves.

### Why Schema Management Matters

Pandera schemas define the expected structure of your data at each layer:

```python
# workflows/schemas/nightscout.py
class RawGlucoseEntries(pa.DataFrameModel):
    """Schema for raw glucose entries from Nightscout API."""

    _id: str = pa.Field(description="Nightscout entry ID")
    sgv: int = pa.Field(ge=20, le=600, description="Glucose in mg/dL")
    dateString: str = pa.Field(description="ISO timestamp string")
    direction: str = pa.Field(nullable=True)
```

As your platform grows, you'll have dozens of schemas. The CLI helps you manage them.

### Discovering Schemas

```bash
$ phlo schema list

Available Schemas
Name                     Fields  Module
────────────────────────────────────────────────
FactDailyMetrics           15   workflows.schemas.nightscout
FactGlucoseReadings        12   workflows.schemas.nightscout
MartGlucoseOverview         6   workflows.schemas.nightscout
RawGlucoseEntries           8   workflows.schemas.nightscout
RawWeatherObservations     10   workflows.schemas.weather
```

### Inspecting Schema Details

```bash
$ phlo schema show RawGlucoseEntries

RawGlucoseEntries
Module: workflows.schemas.nightscout
Fields: 8

Fields
Name         Type     Required  Description
────────────────────────────────────────────
_id          str      ✓
sgv          int      ✓
dateString   str      ✓
direction    str
device       str
type         str
```

You can also view the Iceberg schema equivalent:

```bash
$ phlo schema show RawGlucoseEntries --iceberg
```

### Comparing Schema Versions

When schemas change, use `diff` to understand what's different:

```bash
$ phlo schema diff RawGlucoseEntries --old HEAD~5

Schema Diff: RawGlucoseEntries

Added:
  + transmitter_id: str (optional) - "CGM transmitter serial"

Modified:
  ~ sgv: constraint changed
    - was: ge=0, le=500
    + now: ge=20, le=600

Removed:
  - legacy_timestamp: str

Classification: WARNING (1 safe, 1 warning, 0 breaking)
```

---

## Browsing Your Catalog via CLI

While OpenMetadata provides a powerful UI, you can also explore your catalog from the command line.

### Listing Tables

View all Iceberg tables in your catalog:

```bash
$ phlo catalog tables

Iceberg Tables (ref: main)
Namespace  Table Name              Full Name
──────────────────────────────────────────────────
raw        glucose_entries         raw.glucose_entries
bronze     stg_glucose_entries     bronze.stg_glucose_entries
silver     fct_glucose_readings    silver.fct_glucose_readings
gold       fct_daily_glucose_metrics  gold.fct_daily_glucose_metrics

Total: 4 tables
```

Filter by namespace:

```bash
$ phlo catalog tables --namespace silver
```

### Describing Table Metadata

View detailed schema information:

```bash
$ phlo catalog describe raw.glucose_entries

Table: raw.glucose_entries
Location: s3://lake/warehouse/raw/glucose_entries
Current Snapshot ID: 1234567890
Format Version: 2

Schema:
Column Name        Type      Required
───────────────────────────────────────
_id                string    ✓
sgv                int       ✓
dateString         string    ✓
direction          string
device             string
```

### Viewing Table History

Check snapshot history to understand table evolution:

```bash
$ phlo catalog history raw.glucose_entries

Snapshot History: raw.glucose_entries
Snapshot ID   Timestamp            Operation  Current
─────────────────────────────────────────────────────────
abc12345...   2025-11-27 10:35:00  append     ●
def67890...   2025-11-27 09:30:00  append
ghi12345...   2025-11-27 08:25:00  append

Showing 3 most recent snapshots
```

> **Future Feature:** Automated metadata sync to OpenMetadata (`phlo catalog sync`) is planned for a future release. For now, use OpenMetadata's built-in ingestion pipelines as described in the [setup guide](../setup/openmetadata.md).

---

## Exposing Data via APIs

Your data platform isn't just for analysts running SQL. Applications, mobile apps, and external partners often need API access to your curated datasets.

### The API Layer Problem

```
Traditional approach:

1. Data team builds mart table
2. Backend team builds REST endpoint
3. They disagree on schema
4. Manual sync between dbt model and API
5. Schema changes break integrations
6. Nobody knows what APIs exist
```

Phlo automates this with PostgREST (REST) and Hasura (GraphQL).

> **Implementation Details:** For comprehensive API setup guides, see:
>
> - [docs/setup/postgrest.md](/home/user/phlo/docs/setup/postgrest.md) - PostgREST configuration
> - [docs/setup/hasura.md](/home/user/phlo/docs/setup/hasura.md) - Hasura GraphQL setup

### Auto-Generating REST APIs with PostgREST

PostgREST turns PostgreSQL tables into REST endpoints automatically. The challenge is keeping API views in sync with your dbt models.

**The manual way:**

```sql
-- Write this by hand for every model
CREATE VIEW api.glucose_readings AS
SELECT reading_id, timestamp, sgv, direction
FROM marts_postgres.mrt_glucose_readings;

GRANT SELECT ON api.glucose_readings TO analyst;
```

**The automated way:**

```bash
$ phlo postgrest generate-views

Generating API views from dbt models...

Source: dbt manifest (12 models in marts_postgres)

Views to generate:
  api.glucose_readings     <- mrt_glucose_readings (tag: api)
  api.daily_metrics       <- mrt_daily_glucose_metrics (tag: api)
  api.user_summary        <- mrt_user_summary (tag: api, analyst)

Permissions:
  api.glucose_readings: analyst, admin
  api.daily_metrics: analyst, admin
  api.user_summary: admin (restricted)

Generated SQL saved to: api_views.sql

Apply with: phlo postgrest generate-views --apply
```

### How View Generation Works

1. Phlo reads your dbt `manifest.json`
2. Filters models tagged with `api` (configurable)
3. Generates `CREATE VIEW` statements
4. Maps dbt tags to PostgreSQL roles
5. Optionally applies Row-Level Security

In your dbt model:

```yaml
# models/marts_postgres/mrt_glucose_readings.yml
models:
  - name: mrt_glucose_readings
    description: "Curated glucose readings for API access"
    config:
      tags: ["api", "analyst"] # Exposed to API, readable by analyst role
    columns:
      - name: reading_id
        description: "Unique reading identifier"
      - name: sgv
        description: "Glucose value in mg/dL"
```

Generated SQL:

```sql
-- Auto-generated by: phlo postgrest generate-views
-- Source: mrt_glucose_readings
-- Tags: api, analyst

CREATE OR REPLACE VIEW api.glucose_readings AS
SELECT
    reading_id,
    timestamp,
    sgv,
    direction,
    device
FROM marts_postgres.mrt_glucose_readings;

COMMENT ON VIEW api.glucose_readings IS 'Curated glucose readings for API access';

-- Permissions from tags
GRANT SELECT ON api.glucose_readings TO analyst;
GRANT SELECT ON api.glucose_readings TO admin;
```

### GraphQL with Hasura

For richer query capabilities, Phlo integrates with Hasura:

```bash
# Auto-track new tables in Hasura
$ phlo hasura track

✓ Tracked 3/3 tables
```

You can also set up relationships and permissions:

```bash
# Auto-create relationships from foreign keys
$ phlo hasura relationships

✓ Created 1/1 relationships

# Set up default permissions
$ phlo hasura permissions

✓ Created 6/6 permissions
```

Or do all three at once:

```bash
$ phlo hasura auto-setup

Auto-tracking tables, setting up relationships and permissions...
✓ Complete
```

Now you get GraphQL automatically:

```graphql
query {
  glucose_readings(
    where: { sgv: { _gt: 180 } }
    order_by: { timestamp: desc }
    limit: 10
  ) {
    reading_id
    timestamp
    sgv
    direction
  }
}
```

### Permission Management

Define permissions in YAML, sync to Hasura:

```yaml
# hasura-permissions.yaml
tables:
  api.glucose_readings:
    select:
      anon: false # No public access
      analyst:
        columns: [reading_id, timestamp, sgv, direction]
        filter: {} # All rows
      admin:
        columns: "*" # All columns
        filter: {}

  api.user_summary:
    select:
      analyst: false # Restricted
      admin:
        columns: "*"
        filter: {}
```

Apply permissions from a config file:

```bash
$ phlo hasura sync-permissions --config hasura-permissions.yaml

✓ Permissions synced
```

### When to Use REST vs GraphQL

| Use Case                        | Recommendation     |
| ------------------------------- | ------------------ |
| Simple CRUD operations          | REST (PostgREST)   |
| Mobile apps with varied queries | GraphQL (Hasura)   |
| External partner integrations   | REST (simpler)     |
| Internal dashboards             | GraphQL (flexible) |
| High-volume batch reads         | Direct SQL         |

### API Layer in the Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Consumers                               │
│  Mobile App    Web App    Partner API    Internal Tools     │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌─────────────────┐               ┌─────────────────┐
│   PostgREST     │               │     Hasura      │
│   (REST API)    │               │   (GraphQL)     │
└────────┬────────┘               └────────┬────────┘
         │                                   │
         └─────────────────┬─────────────────┘
                           │
                           ▼
                ┌─────────────────┐
                │   PostgreSQL    │
                │   api schema    │
                │   (views)       │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  marts_postgres │
                │  (dbt models)   │
                └─────────────────┘
```

---

## Best Practices

1. **Document Everything**: Add descriptions to all tables and columns
2. **Use Tags**: Create a consistent tagging strategy (layers, domains, sensitivity)
3. **Set Ownership**: Assign owners to all datasets
4. **Regular Updates**: Run `phlo catalog sync` daily to keep metadata fresh
5. **Quality Checks**: Link data quality tests to tables
6. **Glossary**: Maintain business terms for domain-specific language
7. **Data Contracts**: Define contracts for critical datasets with clear SLAs

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
