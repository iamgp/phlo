# phlo-dbt

dbt transformation integration for Phlo.

## Description

Integrates dbt (data build tool) with the Phlo lakehouse. Provides Dagster assets from dbt models, CLI commands, and automatic project discovery.

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

## Auto-Configuration

This package is **fully auto-configured**:

| Feature               | How It Works                                                            |
| --------------------- | ----------------------------------------------------------------------- |
| **Project Discovery** | Auto-discovers `dbt_project.yml` in workspace via `find_dbt_projects()` |
| **Dagster Assets**    | Automatically creates Dagster assets from dbt models                    |
| **Lineage Events**    | Emits lineage events during model execution                             |
| **Auto-Compile**      | Compiles dbt on Dagster startup via post_start hook                     |

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

# Generate dbt docs
phlo dbt docs generate
```

### Programmatic

```python
from phlo_dbt.discovery import find_dbt_projects, get_dbt_project_dir

# Find all dbt projects in workspace
projects = find_dbt_projects()

# Get the active dbt project directory
project_dir = get_dbt_project_dir()
```

## Entry Points

- `phlo.plugins.dagster` - Provides `DbtDagsterPlugin` for asset definitions
- `phlo.plugins.cli` - Provides `dbt` CLI commands
