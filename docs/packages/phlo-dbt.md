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

| Variable            | Default                               | Description                   |
| ------------------- | ------------------------------------- | ----------------------------- |
| `DBT_PROJECT_DIR`   | `workflows/transforms/dbt`                      | Path to dbt project directory |
| `DBT_PROFILES_DIR`  | `workflows/transforms/dbt/profiles`             | Path to dbt profiles          |
| `DBT_MANIFEST_PATH` | `workflows/transforms/dbt/target/manifest.json` | Path to dbt manifest          |
| `DBT_CATALOG_PATH`  | `workflows/transforms/dbt/target/catalog.json`  | Path to dbt catalog           |

## Features

### Auto-Configuration

| Feature               | How It Works                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| **Project Discovery** | Auto-discovers `dbt_project.yml` in workspace via `find_dbt_projects()` |
| **Asset Specs**       | Automatically creates asset specs from dbt models                        |
| **Lineage Events**    | Emits lineage events during model execution                             |
| **Auto-Compile**      | Compiles dbt on startup via post_start hook                             |

### Discovery Locations

If `DBT_PROJECT_DIR` is set, it is used before discovery.

The discovery module searches these paths in order:

1. `workflows/transforms/dbt/`

## Usage

### CLI Commands

```bash
# Compile dbt project
phlo dbt compile

# Run dbt models
phlo dbt run

# Run specific models
phlo dbt run --select silver.*

# Generate dbt docs
phlo dbt docs generate

# Serve dbt docs
phlo dbt docs serve
```

### Programmatic Access

```python
from phlo_dbt.discovery import find_dbt_projects, get_dbt_project_dir

# Find all dbt projects in workspace
projects = find_dbt_projects()

# Get the active dbt project directory
project_dir = get_dbt_project_dir()
```

## Project Structure

Standard dbt project layout for Phlo:

```
workflows/transforms/dbt/
├── dbt_project.yml
├── profiles.yml
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

| Entry Point            | Plugin                                   |
| ---------------------- | ---------------------------------------- |
| `phlo.plugins.assets` | `DbtAssetProvider` for asset specs       |
| `phlo.plugins.cli`    | `dbt` CLI commands                       |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Dagster adapter for capability specs
- [phlo-trino](phlo-trino.md) - Query engine
- [phlo-iceberg](phlo-iceberg.md) - Table format

## Next Steps

- [dbt Development Guide](../guides/dbt-development.md) - Build transformations
- [Data Modeling Guide](../guides/data-modeling.md) - Bronze/Silver/Gold patterns
- [Workflow Development](../guides/workflow-development.md) - Complete pipelines
