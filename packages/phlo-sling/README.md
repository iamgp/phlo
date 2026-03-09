# phlo-sling

Sling-based database replication ingestion provider for Phlo.

## Overview

`phlo-sling` wraps [Sling](https://slingdata.io/) as a complementary ingestion engine alongside `phlo-dlt`. Sling is a data movement CLI (DB→DB, File→DB, DB→File) with 30+ connectors, optimized for high-speed database replication.

Where DLT excels at API-based ingestion with schema evolution and normalisation, Sling excels at raw-speed database replication with wildcard stream selection (`my_schema.*`), incremental modes, and direct DB-to-DB transfers.

## Installation

```bash
pip install phlo-sling
```

## Usage

### Decorator-Based Replication

```python
import phlo
from phlo_sling import phlo_sling_replication


@phlo_sling_replication(
    stream_name="public.users",
    table_name="users",
    source_conn="PHLO_POSTGRES",
    target_conn="WAREHOUSE",
    group="crm",
    mode="incremental",
    primary_key="id",
    update_key="updated_at",
    cron="0 */2 * * *",
    owner="data-team",
)
def replicate_users(context):
    """Replicate users table from Postgres into raw.users on WAREHOUSE."""
    return None
```

### CLI Commands

```bash
# Run replication from YAML
phlo sling run --replication replications/pg_to_lake.yaml

# Run ad-hoc replication
phlo sling run --source PHLO_POSTGRES --stream public.users --target PHLO_S3 --object raw/users.parquet

# Override the inferred destination object when needed
phlo sling run --source PHLO_POSTGRES --stream public.users --target WAREHOUSE --object raw.users

# List connections
phlo sling conns

# Discover available streams
phlo sling discover PHLO_POSTGRES
phlo sling discover PHLO_POSTGRES --schema public --format json
```

## Configuration

The following environment variables can be used to configure Sling:

- `SLING_DEFAULT_NAMESPACE` - Default namespace for generated replication table names (default: "raw")
- `SLING_DEFAULT_MODE` - Default replication mode (default: "incremental")
- `SLING_AUTO_CONNECTIONS` - Auto-generate Sling connections from Phlo capability metadata (default: true)

Notes:

- Decorator-backed replications need a real Sling destination. When `target_conn` is set and `object` is omitted, `phlo-sling` targets `<namespace>.<table_name>` automatically.
- If you set `SLING_AUTO_CONNECTIONS=false`, `phlo-sling` stops injecting `PHLO_POSTGRES` / `PHLO_S3` connection definitions into the environment.
