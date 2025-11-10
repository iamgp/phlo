# Part 4: Project Nessie—Git-Like Versioning for Data

Iceberg gave us time travel. Now let's add **branching**, **merging**, and **tags** to our data with Project Nessie.

## Why Nessie? The Git Analogy

You already know Git:

```bash
# Code versioning
git branch feature/new-glucose-model
git commit -m "Add glucose categories"
git push origin feature/new-glucose-model
git pull request  # Review changes
git merge  # Promote to main
```

Nessie brings this same workflow to **data**:

```sql
-- Data versioning
BRANCH INTO dev FROM main  -- Create dev branch from main
-- Work on dev branch, transform data
MERGE dev INTO main  -- Promote to production
-- Tag for releases: v1.0, v1.1, etc.
```

## The Problem Nessie Solves

Without versioning, data work looks like:

```
Production Data
    ↓
  (Dev transforms it)
    ↓
  (Oops! Broke something)
    ↓
Production Data is CORRUPTED
    ↓
(Back up from last night? Lost today's data!)
```

With Nessie:

```
main (production)
  ↓
  ├─ dev (development)
  │   └─ (Test transformations)
  │   └─ (Validate quality)
  │   └─ (If bad, delete branch, main unchanged)
  │
  └─ (If good, merge dev → main atomically)
```

## Core Nessie Concepts

### 1. Branches

A branch is an **independent copy of all table metadata**.

```
Database State:
├── main (production)
│   ├── raw.glucose_entries (snapshot v1)
│   ├── bronze.stg_entries (snapshot v3)
│   └── silver.fct_readings (snapshot v5)
│
└── dev (development, created from main)
    ├── raw.glucose_entries (snapshot v1) ← same as main
    ├── bronze.stg_entries (snapshot v3) ← same as main
    └── silver.fct_readings (snapshot v5) ← same as main
```

Now you work on dev:

```
After transformations on dev:
├── main (unchanged)
│   ├── raw.glucose_entries (snapshot v1)
│   ├── bronze.stg_entries (snapshot v3)
│   └── silver.fct_readings (snapshot v5)
│
└── dev (has new snapshots)
    ├── raw.glucose_entries (snapshot v1) ← unchanged
    ├── bronze.stg_entries (snapshot v4) ← NEW
    └── silver.fct_readings (snapshot v6) ← NEW
```

### 2. Commits and Merges

Each change on a branch creates a **commit** (pointer to metadata).

```
Branch History:
main:
  ├── Commit A: Initial data load
  ├── Commit B: Quality fixes
  └── Commit C: Schema evolution (HEAD)

dev (branched from Commit B):
  ├── Commit B': Quality fixes (inherited)
  ├── Commit D: New transformations
  └── Commit E: Schema optimizations (HEAD)

Merge dev → main:
  ├── Commit A: Initial data load
  ├── Commit B: Quality fixes
  ├── Commit C: Schema evolution
  ├── Commit F: Merge commit (combines D + E)
  └── (now HEAD points to F)
```

### 3. Tags (Releases)

Tag specific commits for releases:

```
main:
  ├── Commit A
  ├── Commit B (tag: v1.0-released)
  ├── Commit C
  └── Commit D (tag: v1.1-released, HEAD)

-- Query data as it was at v1.0:
SELECT * FROM iceberg.silver.fct_readings
FOR TAG v1.0-released;
```

## Nessie in Cascade

### Setup: Nessie Runs in Docker

```bash
# Nessie REST API is available at port 19120
curl http://localhost:19120/api/v2/config

# Response:
# {
#   "defaultBranch": "main",
#   "maxSupportedApiVersion": "2",
#   "repositories": []
# }
```

### Default: main Branch

When you start Cascade, the `main` branch exists:

```bash
# List branches
curl http://localhost:19120/api/v2/trees

# Response:
# {
#   "trees": [
#     {
#       "name": "main",
#       "hash": "abc123def456"
#     }
#   ]
# }
```

### Creating a Development Branch

In Cascade, Dagster automatically creates `dev` branch:

```python
# From src/cascade/defs/nessie/operations.py

@asset(name="nessie_dev_branch")
def create_dev_branch(nessie_client: NessieResource) -> None:
    """Ensure dev branch exists for safe transformations."""
    
    # List existing branches
    branches = nessie_client.list_branches()
    branch_names = [b.name for b in branches]
    
    # Create dev if it doesn't exist
    if 'dev' not in branch_names:
        nessie_client.create_branch(
            name='dev',
            from_branch='main'
        )
        print("Created dev branch from main")
    else:
        print("Dev branch already exists")
```

### Cascade's Development Workflow

Here's how Cascade uses Nessie branches:

```
1. INGEST TO DEV
   ┌──────────────────────┐
   │ nessie_dev_branch    │ ← Ensure dev exists
   └──────────┬───────────┘
              ↓
   ┌──────────────────────────┐
   │ dlt_glucose_entries      │ ← Ingest to raw.entries
   │ (branch: dev)            │   (creates new snapshot on dev)
   └──────────┬───────────────┘

2. TRANSFORM ON DEV
              ↓
   ┌──────────────────────────┐
   │ dbt_bronze, silver, gold │ ← Transform (new snapshots)
   │ (branch: dev)            │
   └──────────┬───────────────┘

3. VALIDATE QUALITY
              ↓
   ┌──────────────────────────┐
   │ Data quality checks      │ ← Tests, assertions
   │ (branch: dev)            │
   └──────────┬───────────────┘
              ↓ (if OK)
   
4. MERGE TO MAIN
   ┌──────────────────────────┐
   │ promote_dev_to_main      │ ← Atomic merge
   └──────────┬───────────────┘
              ↓
   ┌──────────────────────────┐
   │ main branch now has      │ ← Production data
   │ latest transformations   │   ready to use
   └──────────────────────────┘
```

### Code: Merge from Dev to Main

```python
# From src/cascade/defs/nessie/workflow.py

@asset(deps=[nessie_dev_branch, "dbt:*", "quality_checks"])
def promote_dev_to_main(nessie_client: NessieResource) -> None:
    """
    Merge dev branch to main after validation.
    
    Ensures all transformation and quality checks pass
    before promoting to production.
    """
    
    nessie_client.merge_branch(
        from_branch='dev',
        to_branch='main',
        message='Promote validated transforms to production'
    )
    
    print("✓ Data promoted from dev to main")
    print("✓ All tables on main branch updated atomically")
```

This ensures:
- Dev branch never affects main
- Merge is atomic (all tables or none)
- Audit trail (who merged what, when)

## Hands-On: Explore Nessie

### List All Branches

```bash
curl http://localhost:19120/api/v2/trees

# Response (pretty-printed):
# {
#   "trees": [
#     {
#       "name": "main",
#       "hash": "def456xyz"
#     },
#     {
#       "name": "dev",
#       "hash": "abc123def"
#     }
#   ]
# }
```

### View Branch History

```bash
# Get commit history for a branch
curl "http://localhost:19120/api/v2/trees/main/history" \
  -H "Content-Type: application/json" \
  -d '{
    "maxResults": 10,
    "pageToken": null
  }'

# Response:
# {
#   "logEntries": [
#     {
#       "commitMeta": {
#         "hash": "abc123def456",
#         "message": "Promote validated transforms to production",
#         "authorTime": 1729027800000,
#         "commitTime": 1729027800000
#       },
#       "operations": [
#         {
#           "type": "Put",
#           "key": {
#             "elements": ["silver", "fct_glucose_readings"]
#           }
#         }
#       ]
#     }
#   ]
# }
```

### Query on a Specific Branch

When using Trino with Nessie, you select which branch:

```sql
-- Query main (production)
SET SESSION iceberg.nessie_reference_name = 'main';
SELECT COUNT(*) FROM iceberg.raw.glucose_entries;
-- Result: 5000

-- Query dev (development)
SET SESSION iceberg.nessie_reference_name = 'dev';
SELECT COUNT(*) FROM iceberg.raw.glucose_entries;
-- Result: 5500 (includes new test data)

-- Switch back to main
SET SESSION iceberg.nessie_reference_name = 'main';
SELECT COUNT(*) FROM iceberg.raw.glucose_entries;
-- Result: 5000 (unchanged)
```

In dbt, this is automatic—it reads from the configured branch:

```yaml
# transforms/dbt/profiles.yml

cascade:
  outputs:
    dev:
      type: trino
      host: trino
      catalog: iceberg
      schema: bronze
      session_properties:
        iceberg.nessie_reference_name: dev  ← Run on dev branch
        
    prod:
      type: trino
      host: trino
      catalog: iceberg
      schema: bronze
      session_properties:
        iceberg.nessie_reference_name: main  ← Run on main branch
```

## Advanced: Manual Branch Operations

```bash
# Create a feature branch
curl -X "POST" http://localhost:19120/api/v2/trees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "feature/new-metrics",
    "hash": "main"  # Branch from main
  }'

# Make changes on feature branch
# (Nessie tables automatically point to this branch)

# If changes are good, merge to dev
curl -X "POST" http://localhost:19120/api/v2/trees/dev/commits \
  -H "Content-Type: application/json" \
  -d '{
    "fromBranch": "feature/new-metrics",
    "message": "Merge new metrics into dev"
  }'

# Clean up feature branch
curl -X "DELETE" http://localhost:19120/api/v2/trees/feature/new-metrics
```

## Nessie vs Iceberg: Understanding the Layers

```
┌────────────────────────────────────────────────┐
│ Nessie (Catalog Layer)                         │
│ - Branch: main, dev, feature/metrics           │
│ - Commit: "Promote validated data"             │
│ - References: Which branch has which tables    │
└────────────────────┬─────────────────────────┘
                     │ (Points to)
┌────────────────────▼──────────────────────────┐
│ Iceberg (Table Format Layer)                   │
│ - Snapshot: v1.metadata.json                  │
│ - Manifest: Files in this snapshot             │
│ - Data: S3 parquet files                       │
└────────────────────────────────────────────────┘
```

**Nessie** = "which version of which table per branch"
**Iceberg** = "what files make up this table version"

Together: Complete versioning from storage to queries.

## Real-World Scenario: Handling a Bug

Let's say your transformation has a bug:

```sql
-- Bug: All glucose values are multiplied by 2!
SELECT glucose_mg_dl * 2 as glucose_mg_dl  -- WRONG
FROM stg_glucose_entries;
```

### Without Nessie (Disaster)

```
1. Bug deployed to main
   ↓ Production dashboards show 2x glucose values
   ↓ People think blood sugar is spiking
   ↓ Alerts fire for high glucose
   ↓ (This happened to real patients, very bad)
   ↓
2. Discover bug 2 hours later
   ↓
3. Fix and re-run
   ↓
4. Need to clean up corrupted 2 hours of data (hard!)
   ↓
5. Audit trail: ? (who made the change?)
```

### With Nessie (Safe)

```
1. Bug caught during dev branch testing
   ↓ Run quality checks on dev branch
   ↓ Tests fail: "glucose_mg_dl should be < 500"
   ↓
2. Fix bug, re-run on dev
   ↓ Tests pass
   ↓
3. Merge dev → main only when validated
   ↓ main branch still shows correct data
   ↓
4. Audit trail: commit "Fix glucose calculation bug"
   ↓ Can query dev branch to see what was wrong
```

## Cascade's Nessie Configuration

In `docker-compose.yml`:

```yaml
nessie:
  image: ghcr.io/projectnessie/nessie:${NESSIE_VERSION}
  environment:
    NESSIE_VERSION_STORE_TYPE: JDBC
    # Nessie metadata stored in Postgres
    QUARKUS_DATASOURCE_JDBC_URL: jdbc:postgresql://postgres:5432/lakehouse
    # Iceberg warehouse location
    nessie.catalog.warehouses.warehouse.location: s3://lake/warehouse
    # MinIO S3 access
    nessie.catalog.service.s3.default-options.endpoint: http://minio:9000/
    nessie.catalog.service.s3.default-options.access-key: minioadmin
    nessie.catalog.service.s3.default-options.secret: minioadmin
```

Breaking this down:
- **JDBC**: Nessie metadata (commits, branches) in Postgres
- **Warehouse**: Iceberg data files in MinIO S3
- **S3 access**: Credentials for MinIO

## Next: Data Ingestion

Now we understand:
- Iceberg: Table format with snapshots and time travel
- Nessie: Git-like branching on top of Iceberg

Next: How does data actually get into this system?

**Part 5: Data Ingestion with DLT and PyIceberg**

See you then!

## Summary

**Project Nessie**:
- Branch isolation (dev/staging/prod)
- Atomic merges (all-or-nothing)
- Commit history (audit trail)
- Tags for releases
- REST API for automation

**In Cascade**:
- Automatically creates `dev` branch
- Ingests/transforms on `dev`
- Validates data quality
- Merges to `main` when production-ready
- Prevents bugs from reaching production

**Next**: [Part 5: Data Ingestion—Getting Data Into the Lakehouse](05-data-ingestion.md)
