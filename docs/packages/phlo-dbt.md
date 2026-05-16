# phlo-dbt

dbt transformation integration for Phlo.

## Overview

`phlo-dbt` integrates dbt (data build tool) with the Phlo lakehouse. It provides asset specs from dbt models, CLI commands, and automatic project discovery.

## Installation

```bash
pip install phlo-dbt
# or
phlo plugin install dbt
```

## Configuration

| Variable                  | Default                               | Description                                  |
| ------------------------- | ------------------------------------- | -------------------------------------------- |
| `DBT_PROJECT_DIR`         | `workflows/transforms/dbt`            | Path to dbt project directory                |
| `DBT_QUERY_ENGINE_TYPE`   | `trino`                               | Adapter type written into generated profiles |
| `DBT_QUERY_HOST`          | `trino`                               | Query engine host                            |
| `DBT_QUERY_PORT`          | `8080`                                | Query engine port                            |
| `DBT_QUERY_CATALOG`       | `iceberg`                             | Base query engine catalog                    |
| `DBT_QUERY_SCHEMA`        | `raw`                                 | Default schema                               |
| `DBT_QUERY_USER`          | `dagster`                             | Query engine user                            |
| `DBT_QUERY_HTTP_SCHEME`   | `http`                                | Query engine scheme                          |
| `DBT_QUERY_AUTH_METHOD`   | `none`                                | Query engine auth method                     |
| `DBT_QUERY_THREADS`       | `2`                                   | dbt worker threads                           |

Paths for `profiles/` and `target/` artifacts are derived from `DBT_PROJECT_DIR`:
- Profiles: `{DBT_PROJECT_DIR}/profiles`
- Manifest: `{DBT_PROJECT_DIR}/target/manifest.json`
- Catalog: `{DBT_PROJECT_DIR}/target/catalog.json`

## Features

### Auto-Configuration

| Feature               | How It Works                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| **Project Discovery** | Auto-discovers `dbt_project.yml` in workspace via `find_dbt_projects()` |
| **Generated Profiles**| Writes canonical `profiles.yml` from Phlo runtime settings             |
| **Asset Specs**       | Automatically creates asset specs from dbt models                      |
| **Lineage Events**    | Emits lineage events during model execution                            |
| **Auto-Compile**      | Compiles dbt on startup via post_start hook                            |
| **Fail-Closed Setup** | Existing dbt projects fail startup if manifest/profile setup is broken |

### Discovery Locations

If `DBT_PROJECT_DIR` is set, it is used before discovery.

The discovery module searches these paths in order:

1. `workflows/transforms/dbt/`

## Usage

### CLI Commands

```bash
# Compile dbt project
phlo dbt compile

# Run dbt in the active orchestrator service container
phlo dbt run

# Run specific models
phlo dbt run --select silver.*

# Run host dbt directly
phlo dbt test --local --select gold.*
```

When `.phlo/` exists, `phlo dbt compile|run|test` executes inside the running `dagster`
service by default. That keeps dbt aligned with the project's active Trino, Iceberg, and
generated profile configuration. Use `--local` when you explicitly want host dbt.
After a successful `phlo dbt run`, Phlo also imports manifest asset lineage into the
configured lineage sink when one is installed.

### Programmatic Access

```python
from phlo_dbt import build_partition_vars, extract_manifest_tables, normalize_selectors
from phlo_dbt.discovery import find_dbt_projects, get_dbt_project_dir

# Find all dbt projects in workspace
projects = find_dbt_projects()

# Get the active dbt project directory
project_dir = get_dbt_project_dir()

# Normalize selectors and prepare partition vars for model execution
selectors = normalize_selectors("silver.*, gold.mart_orders")
vars_ = build_partition_vars(partition_key="2026-05-16")
```

### Helper Utilities

`phlo-dbt` exposes lightweight helpers for workflow authors:

| Helper | Purpose |
| --- | --- |
| `normalize_selectors` | Normalize comma/space-separated selector input. |
| `select_manifest_models` | Select simple dbt model nodes from a manifest. |
| `extract_manifest_tables` | Extract model table references from a manifest. |
| `build_partition_vars` | Build dbt vars for partitioned runs. |
| `ensure_compiled` | Ensure the active dbt project has a manifest. |

### Runtime routing

`phlo-dbt` derives its active target from canonical runtime routing:

- explicit target argument
- runtime `environment`
- legacy `dbt_target` tag only as fallback

When the runtime carries a ref, dbt also uses a ref-aware catalog name such as
`iceberg_feature_orders`.

### Generated profiles

Do not hand-maintain environment-specific dbt profiles inside Phlo projects.

`phlo-dbt` generates `workflows/transforms/dbt/profiles/profiles.yml` from its
own runtime settings so dbt remains capability-driven and does not need to import
concrete query-engine packages.

## Project Structure

Standard dbt project layout for Phlo:

```
workflows/transforms/dbt/
├── dbt_project.yml
├── profiles/
│   └── profiles.yml
├── models/
│   ├── bronze/           # Staging models
│   │   └── stg_*.sql
│   ├── silver/           # Cleaned models
│   │   └── *.sql
│   └── gold/             # Mart models
│       └── mrt_*.sql
├── macros/
├── seeds/
└── target/               # Compiled artifacts
    ├── manifest.json
    └── catalog.json
```

## Bronze/Silver/Gold Pattern

### Bronze (Staging)

```sql
-- models/bronze/stg_events.sql
{{ config(materialized='incremental', unique_key='id') }}

SELECT
    id,
    timestamp,
    user_id,
    event_type
FROM {{ source('raw', 'events') }}
{% if is_incremental() %}
WHERE timestamp > (SELECT MAX(timestamp) FROM {{ this }})
{% endif %}
```

### Silver (Cleaned)

```sql
-- models/silver/events_cleaned.sql
{{ config(materialized='table') }}

SELECT
    id,
    timestamp,
    user_id,
    UPPER(event_type) as event_type,
    DATE(timestamp) as event_date
FROM {{ ref('stg_events') }}
WHERE user_id IS NOT NULL
```

### Gold (Marts)

```sql
-- models/gold/mrt_daily_events.sql
{{ config(materialized='table') }}

SELECT
    event_date,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users
FROM {{ ref('events_cleaned') }}
GROUP BY 1, 2
```

## Entry Points

| Entry Point                   | Plugin                                   |
| ----------------------------- | ---------------------------------------- |
| `phlo.plugins.assets`         | `DbtAssetProvider` for asset specs       |
| `phlo.plugins.transformation_providers` | `DbtTransformationProvider` for transforms |
| `phlo.plugins.cli`            | `DbtCliPlugin` for dbt CLI commands      |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Dagster adapter for capability specs
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-iceberg](phlo-iceberg.md) - Table format
- [Integration Profiles](../guides/integration-profiles.md) - Supported capability combinations

## Next Steps

- [dbt Development Guide](../guides/dbt-development.md) - Build transformations
- [Data Modeling Guide](../guides/data-modeling.md) - Bronze/Silver/Gold patterns
- [Workflow Development](../guides/workflow-development.md) - Complete pipelines
