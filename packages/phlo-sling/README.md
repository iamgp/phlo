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
    group="crm",
    mode="incremental",
    primary_key="id",
    update_key="updated_at",
    cron="0 */2 * * *",
    owner="data-team",
)
def replicate_users(context):
    """Replicate users table from Postgres to table store."""
    return None
```

### CLI Commands

```bash
# Run replication from YAML
phlo sling run --replication replications/pg_to_lake.yaml

# Run ad-hoc replication
phlo sling run --source PHLO_POSTGRES --stream public.users --target PHLO_S3

# List connections
phlo sling conns

# Discover available streams
phlo sling discover PHLO_POSTGRES
```

## Configuration

The following environment variables can be used to configure Sling:

- `SLING_DEFAULT_NAMESPACE` - Default namespace for generated replication table names (default: "raw")
- `SLING_DEFAULT_MODE` - Default replication mode (default: "incremental")
- `SLING_AUTO_CONNECTIONS` - Auto-generate Sling connections from Phlo capability metadata (default: true)
