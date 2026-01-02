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

```
main branch (production)     dev branch (development)
      │                            │
      │  ← stable, validated       │  ← experimental, testing
      │                            │
      └──── merge when ready ──────┘
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

## Nessie in Phlo

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

When you start Phlo, the `main` branch exists:

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

In Phlo, Dagster automatically creates `dev` branch:

```python
# From workflows/nessie/operations.py

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

### Phlo's Write-Audit-Publish Pattern

Phlo implements the **Write-Audit-Publish (WAP)** pattern automatically:

```
┌─────────────────────────────────────────────────────────────────┐
│                     FEATURE BRANCH (dev)                         │
│  Catalog: iceberg_dev                                           │
│                                                                  │
│  1. Ingestion ──► 2. Transforms (dbt) ──► 3. Quality Checks     │
│     (PyIceberg)      (bronze→silver→gold)    (validation)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 4. All Checks Pass?
                              ▼
                    ┌─────────────────┐
                    │  AUTO-MERGE     │ (Nessie merge via sensor)
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MAIN BRANCH                                │
│  Catalog: iceberg                                               │
│                                                                  │
│  5. Publishing ──► Postgres (marts for BI dashboards)           │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight**: All writes happen on the feature branch. Only validated data reaches main.

### Automatic Branch Management with Sensors

Phlo handles branching automatically via Dagster sensors:

```python
# 1. branch_creation_sensor - Creates branch when pipeline starts
@run_status_sensor(run_status=DagsterRunStatus.STARTING)
def branch_creation_sensor(context, branch_manager):
    """Auto-create pipeline/run-{id} branch for isolation."""
    branch_manager.create_pipeline_branch(context.dagster_run.run_id)

# 2. auto_promotion_sensor - Merges when quality checks pass
@sensor(minimum_interval_seconds=30)
def auto_promotion_sensor(context, nessie, branch_manager):
    """Auto-merge to main when all ERROR-severity checks pass."""
    # Check recent runs for passing quality checks
    # If all pass → merge branch to main
    # Create timestamped tag (v20251126_143000)

# 3. branch_cleanup_sensor - Deletes old branches
@sensor(minimum_interval_seconds=3600)
def branch_cleanup_sensor(context, branch_manager):
    """Clean up branches after retention period (default: 7 days)."""
```

**You don't need to manually merge** - the sensor handles it when quality checks pass.

### Trino Catalog Configuration (Not Session Properties)

Nessie branching in Trino is configured at the **catalog level**, not via session properties:

```properties
# .phlo/trino/catalog/iceberg.properties (main branch)
connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://nessie:19120/iceberg/main
iceberg.rest-catalog.prefix=main
```

```properties
# .phlo/trino/catalog/iceberg_dev.properties (dev branch)
connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://nessie:19120/iceberg/dev
iceberg.rest-catalog.prefix=dev
```

Query different branches by using different catalogs:

```sql
-- Query main (production)
SELECT COUNT(*) FROM iceberg.raw.glucose_entries;

-- Query dev (development)
SELECT COUNT(*) FROM iceberg_dev.raw.glucose_entries;
```

### Using Branch in Code

```python
from phlo_trino.resource import TrinoResource

trino = TrinoResource()

# Query main branch (default)
rows = trino.execute("SELECT * FROM iceberg.marts.readings", branch="main")

# Query dev branch
rows = trino.execute("SELECT * FROM iceberg_dev.marts.readings", branch="dev")
```

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

Use different Trino catalogs to query different branches:

```sql
-- Query main (production) - uses 'iceberg' catalog
SELECT COUNT(*) FROM iceberg.raw.glucose_entries;
-- Result: 5000

-- Query dev (development) - uses 'iceberg_dev' catalog
SELECT COUNT(*) FROM iceberg_dev.raw.glucose_entries;
-- Result: 5500 (includes new test data)

-- Compare between branches
SELECT
    'main' as branch, COUNT(*) as rows FROM iceberg.raw.glucose_entries
UNION ALL
SELECT
    'dev' as branch, COUNT(*) as rows FROM iceberg_dev.raw.glucose_entries;
```

In dbt, select the target to use the appropriate catalog:

```yaml
# workflows/transforms/dbt/profiles.yml

phlo:
  outputs:
    dev:
      type: trino
      host: trino
      catalog: iceberg_dev # ← Dev branch catalog
      schema: bronze

    prod:
      type: trino
      host: trino
      catalog: iceberg # ← Main branch catalog
      schema: bronze
```

```bash
# Run dbt on dev branch
dbt run --target dev

# Run dbt on main branch (production)
dbt run --target prod
```

## Advanced: Manual Branch Operations

Using the Nessie REST API (v1):

```bash
# Get main branch hash
MAIN_HASH=$(curl -s http://localhost:19120/api/v1/trees/tree/main | jq -r '.hash')

# Create a feature branch from main
curl -X POST http://localhost:19120/api/v1/trees/tree \
  -H "Content-Type: application/json" \
  -d "{\"type\": \"BRANCH\", \"name\": \"feature/new-metrics\", \"hash\": \"$MAIN_HASH\"}"

# List all branches
curl -s http://localhost:19120/api/v1/trees | jq '.references[].name'

# Merge feature branch to main
TARGET_HASH=$(curl -s http://localhost:19120/api/v1/trees/tree/main | jq -r '.hash')
SOURCE_HASH=$(curl -s http://localhost:19120/api/v1/trees/tree/feature/new-metrics | jq -r '.hash')

curl -X POST "http://localhost:19120/api/v1/trees/tree/main/merge?expectedHash=$TARGET_HASH" \
  -H "Content-Type: application/json" \
  -d "{\"fromRefName\": \"feature/new-metrics\", \"fromHash\": \"$SOURCE_HASH\"}"

# Delete feature branch after merge
BRANCH_HASH=$(curl -s http://localhost:19120/api/v1/trees/tree/feature/new-metrics | jq -r '.hash')
curl -X DELETE "http://localhost:19120/api/v1/trees/branch/feature/new-metrics?expectedHash=$BRANCH_HASH"
```

Or use the `NessieResource` in Python:

```python
from phlo_nessie.resource import NessieResource

nessie = NessieResource()

# Create branch
nessie.create_branch("feature/new-metrics", source_ref="main")

# Merge branch
nessie.merge_branch("feature/new-metrics", "main")

# Delete branch
nessie.delete_branch("feature/new-metrics")
```

## Branch Management via CLI

The REST API and Python SDK work, but for day-to-day operations, `phlo branch` is simpler.

### List Branches

```bash
$ phlo branch list

Branches:
  NAME                  HASH         TABLES  LAST COMMIT
  main (default)        a1b2c3d4     15      2h ago
  dev                   e5f6g7h8     15      4h ago
  feature/new-metrics   i9j0k1l2     16      1d ago

Tags:
  release-2024-01       m3n4o5p6     15      7d ago
```

### Create a Feature Branch

```bash
# Create from main (default)
$ phlo branch create feature/new-transform

Creating branch: feature/new-transform
Source: main (a1b2c3d4)

✓ Branch created

# Create from specific branch
$ phlo branch create experiment/risky-change --from dev
```

### Compare Branches

See what's different between branches before merging:

```bash
$ phlo branch diff main feature/new-transform

Branch Diff: main ← feature/new-transform
══════════════════════════════════════════

Tables Modified:
  silver.fct_glucose_readings
    + Column: estimated_a1c (float)
    ~ Column: glucose_category (type unchanged, constraint added)

Tables Added:
  gold.dim_glucose_ranges (new table)

Commits on feature/new-transform not in main:
  i9j0k1l2  Add estimated A1C calculation
  k2l3m4n5  Add glucose range dimension

Safe to merge: Yes (no conflicts detected)
```

### Merge Branches

```bash
# Preview merge (dry run)
$ phlo branch merge feature/new-transform main --dry-run

Merge Preview: feature/new-transform → main
════════════════════════════════════════════

Changes to apply:
  + gold.dim_glucose_ranges (new table)
  ~ silver.fct_glucose_readings (schema change)

No conflicts detected.
Run without --dry-run to merge.

# Perform merge
$ phlo branch merge feature/new-transform main

Merging: feature/new-transform → main

✓ Merge successful
  Commit: q8r9s0t1
  Tables affected: 2
```

### Delete Branches

```bash
# Delete merged branch
$ phlo branch delete feature/new-transform

Deleting branch: feature/new-transform

⚠ This branch has been merged to main.
Proceed? [y/N] y

✓ Branch deleted

# Force delete unmerged branch
$ phlo branch delete experiment/abandoned --force
```

### Practical Workflow: Safe Schema Changes

Here's how to use branches for safe data development:

```bash
# 1. Create a feature branch
$ phlo branch create feature/add-a1c-calculation

# 2. Switch Trino to use the branch (in your SQL client)
#    USE iceberg_feature_add_a1c_calculation.silver;

# 3. Make changes (run dbt, materialize assets)
$ dbt run --select fct_glucose_readings
$ phlo materialize fct_glucose_readings --partition 2024-01-15

# 4. Validate changes
$ phlo contract validate glucose_readings
$ phlo quality run silver.fct_glucose_readings

# 5. Compare to main
$ phlo branch diff main feature/add-a1c-calculation

# 6. If everything looks good, merge
$ phlo branch merge feature/add-a1c-calculation main

# 7. Clean up
$ phlo branch delete feature/add-a1c-calculation
```

### Branch Naming Conventions

| Pattern          | Use Case                            |
| ---------------- | ----------------------------------- |
| `feature/xyz`    | New features, schema changes        |
| `fix/xyz`        | Bug fixes to transformations        |
| `experiment/xyz` | Exploratory work (may be abandoned) |
| `release/v1.2`   | Tagged releases for rollback points |
| `dev`            | Shared development branch           |

### When to Use Branches

| Scenario                            | Use Branch?                   |
| ----------------------------------- | ----------------------------- |
| Adding new column to existing table | Yes                           |
| Changing data type                  | Yes                           |
| Testing new transformation logic    | Yes                           |
| Daily data ingestion                | No (use main)                 |
| Bug fix to production               | Yes (then merge quickly)      |
| Exploratory analysis                | Optional (nice for isolation) |

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

## Phlo's Nessie Configuration

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

**In Phlo (Write-Audit-Publish)**:

- `branch_creation_sensor` - Auto-creates pipeline branch on job start
- `auto_promotion_sensor` - Auto-merges to main when quality checks pass
- `branch_cleanup_sensor` - Cleans up old branches after retention period
- Catalog-based branching: `iceberg` (main) vs `iceberg_dev` (dev)
- All writes happen on feature branch - only validated data reaches main

**Next**: [Part 5: Data Ingestion—Getting Data Into the Lakehouse](05-data-ingestion.md)
