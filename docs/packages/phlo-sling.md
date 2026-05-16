# phlo-sling

Sling-based data replication for Phlo.

## Overview

The `phlo-sling` package provides Sling-based data replication capabilities for the Phlo platform, enabling declarative and programmatic definitions of replication pipelines from various sources to target data stores.

## Installation

```bash
pip install phlo-sling
```

Or with the full Phlo distribution:

```bash
pip install phlo[defaults]
```

## Quick Start

Define a Sling replication pipeline using the decorator:

```python
from phlo_sling import phlo_sling_replication

@phlo_sling_replication(
    stream_name="public.users",
    table_name="users",
    source_conn="POSTGRES",
    group="ingestion",
    mode="incremental",
    update_key="updated_at",
)
def replicate_users(context):
    pass
```

## Helper Utilities

`phlo-sling` exposes small helpers for common replication authoring tasks:

```python
from phlo_sling import build_partition_where, build_replication_plan, summarize_connections

where = build_partition_where("updated_at", "2026-05-01", "2026-05-02")
plan = build_replication_plan(
    ["lims.samples", "lims.results"],
    source_conn="LIMS",
    target_conn="PHLO_ICEBERG",
    update_key="updated_at",
    where=where,
)

connections = summarize_connections()
```

| Helper | Purpose |
| --- | --- |
| `build_partition_where` | Build a half-open source window predicate. |
| `table_name_from_stream` | Derive stable target names from stream names. |
| `build_replication_plan` | Build `SlingReplication` objects from stream names or mappings. |
| `summarize_connections` | Display non-secret Sling connection summaries. |

## Decorators

### `@phlo_sling_replication`

Registers a function as a Sling-backed replication asset.

**Parameters:**

**Required:**
- `stream_name` (str): Source stream identifier (e.g., "public.users")
- `table_name` (str): Target table name in the destination
- `source_conn` (str): Sling source connection name (references env vars)
- `group` (str): Asset group name for organization

**Optional:**
- `target_conn` (str | None): Sling target connection name (auto-resolved if not provided)
- `mode` ("full-refresh" | "incremental" | "snapshot" | "backfill"): Replication mode
- `primary_key` (list[str] | str | None): Primary key column(s) for merge operations
- `update_key` (str | None): Update key column for incremental mode (required when mode="incremental")
- `object` (str | None): Target object path for file-based destinations
- `select` (list[str] | None): List of columns to select (empty = all columns)
- `where` (str | None): SQL WHERE clause for source filtering
- `source_options` (dict | None): Additional source-specific Sling options
- `target_options` (dict | None): Additional target-specific Sling options
- `cron` (str | None): Cron schedule for automatic execution
- `freshness_hours` (tuple[int, int] | None): Data freshness SLA as (warning_hours, error_hours)
- `max_runtime_seconds` (int): Maximum execution time before timeout (default: 600)
- `max_retries` (int): Maximum retry attempts on failure (default: 3)
- `retry_delay_seconds` (int): Seconds between retry attempts (default: 30)
- `owner` (str | None): Asset owner identifier
- `consumers` (list[Consumer | str] | None): List of data consumers
- `sla` (SLA | None): Service level agreement definition

**Example:**

```python
@phlo_sling_replication(
    stream_name="public.users",
    table_name="users",
    source_conn="POSTGRES",
    group="ingestion",
    mode="full-refresh",
)
def replicate_users_full(context):
    pass
```

### `@phlo_sling_assets`

Discovers and registers multiple Sling assets from a function.

```python
from phlo_sling import phlo_sling_assets

@phlo_sling_assets(
    source_conn="POSTGRES",
    group="ingestion",
    mode="incremental",
    update_key="updated_at",
)
def discover_tables(context):
    # Return list of table names to replicate
    return ["users", "orders", "products"]
```

## Configuration

### Environment Variables

Configure source connections using environment variables with the connection name prefix:

```bash
# PostgreSQL source (for source_conn="POSTGRES")
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=admin
export POSTGRES_PASSWORD=secret
export POSTGRES_DATABASE=production

# Or for source_conn="PHLO_POSTGRES"
export PHLO_POSTGRES_HOST=localhost
export PHLO_POSTGRES_PORT=5432
export PHLO_POSTGRES_USER=admin
export PHLO_POSTGRES_PASSWORD=secret
export PHLO_POSTGRES_DATABASE=production

# S3 target (via MinIO) for source_conn="S3"
export S3_ENDPOINT=localhost:9000
export S3_ACCESS_KEY=minioadmin
export S3_SECRET_KEY=minioadmin
export S3_BUCKET=my-bucket
```

## Replication Modes

### Full Refresh

Replace entire table on each run:

```python
@phlo_sling_replication(
    stream_name="public.config",
    table_name="config",
    source_conn="POSTGRES",
    group="reference",
    mode="full-refresh",
)
def replicate_config(context):
    pass
```

### Incremental

Only load new/updated rows:

```python
@phlo_sling_replication(
    stream_name="public.events",
    table_name="events",
    source_conn="POSTGRES",
    group="ingestion",
    mode="incremental",
    update_key="created_at",
    primary_key=["id"],
)
def replicate_events(context):
    pass
```

### Snapshot

Point-in-time snapshot:

```python
@phlo_sling_replication(
    stream_name="public.reporting",
    table_name="reporting_snapshot",
    source_conn="POSTGRES",
    group="analytics",
    mode="snapshot",
)
def replicate_reporting(context):
    pass
```

### Backfill

Reprocess historical data:

```python
@phlo_sling_replication(
    stream_name="public.legacy_data",
    table_name="legacy_data",
    source_conn="POSTGRES",
    group="migration",
    mode="backfill",
    primary_key=["id"],
)
def replicate_legacy(context):
    pass
```

## API Reference

### `SlingReplication`

Data class for replication definitions.

```python
from phlo_sling import SlingReplication

replication = SlingReplication(
    stream_name="public.users",
    table_name="users",
    source_conn="POSTGRES",
    mode="incremental",
    update_key="updated_at",
)
```

### `get_sling_assets()`

Retrieve all registered Sling replication asset specifications.

```python
from phlo_sling import get_sling_assets

assets = get_sling_assets()
for asset in assets:
    print(f"Replication: {asset.stream_name} -> {asset.table_name}")
```

### `clear_sling_assets()`

Clear all registered Sling assets from the internal registry. Used primarily for testing.

```python
from phlo_sling import clear_sling_assets

clear_sling_assets()
```

## Best Practices

1. **Use incremental mode** for large tables to minimize load
2. **Set update_key for incremental mode** - required for change detection
3. **Set primary_key** for proper deduplication and merge operations
4. **Group related replications** for better organization
5. **Configure cron schedules** for automatic execution
6. **Set freshness_hours SLA** for data quality monitoring
7. **Test in development** before production deployment

## Troubleshooting

### Connection Errors

Verify environment variables match the `source_conn` name:

```python
# For source_conn="POSTGRES"
# Need: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, etc.

# For source_conn="PHLO_POSTGRES"
# Need: PHLO_POSTGRES_HOST, PHLO_POSTGRES_PORT, etc.
```

### Incremental Mode Requires update_key

If you get an error about missing update_key:

```python
@phlo_sling_replication(
    stream_name="public.users",
    table_name="users",
    source_conn="POSTGRES",
    group="ingestion",
    mode="incremental",
    update_key="updated_at",  # Required for incremental mode!
)
def replicate_users(context):
    pass
```

### Permission Denied

Ensure the database user has SELECT permissions on source tables.

## Entry Points

| Entry Point                    | Plugin                                           |
| ------------------------------ | ------------------------------------------------ |
| `phlo.plugins.assets`          | `SlingAssetProvider` - Asset discovery           |
| `phlo.plugins.cli`             | `SlingCliPlugin` - CLI commands                  |
| `phlo.plugins.ingestion_providers` | `SlingIngestionProvider` - Ingestion backend |

## See Also

- [phlo-dlt](phlo-dlt.md) - Alternative ingestion with DLT
- [phlo-postgres](phlo-postgres.md) - PostgreSQL integration
- [Developer Guide](../guides/developer-guide.md)
- [Sling Documentation](https://docs.sling.io/) - Official Sling docs
