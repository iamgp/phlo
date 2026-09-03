# phlo-clickhouse

ClickHouse analytical database for Phlo.

## Overview

`phlo-clickhouse` provides ClickHouse as a combined `table_store`, `query_engine`, and `publish_target` capability in Phlo. Unlike the existing bundled stack (DLT -> Iceberg -> Trino/dbt -> Postgres), ClickHouse can serve all three data plane roles in a single service.

> **Alternative Data Plane**: ClickHouse is an alternative to the bundled Iceberg/Trino/Postgres stack. Choose this for simpler deployments or teams already invested in the ClickHouse ecosystem.

## Installation

```bash
pip install phlo-clickhouse
# or
phlo plugin install clickhouse
```

## Configuration

| Variable                       | Required | Default                     | Description                    |
| ------------------------------ | -------- | --------------------------- | ------------------------------ |
| `CLICKHOUSE_HOST`              | No       | `clickhouse`                | ClickHouse service hostname    |
| `CLICKHOUSE_HTTP_PORT`         | No       | `8123`                      | ClickHouse HTTP interface port |
| `CLICKHOUSE_NATIVE_PORT`        | No       | `19000`                     | ClickHouse native protocol port |
| `CLICKHOUSE_USER`              | No       | `default`                   | ClickHouse username           |
| `CLICKHOUSE_PASSWORD`          | No       |                             | ClickHouse password           |
| `CLICKHOUSE_DB`                 | No       | `default`                   | Default ClickHouse database   |
| `CLICKHOUSE_SECURE`            | No       | `false`                     | Use TLS for connections       |

## Features

### Auto-Configuration

Works out-of-the-box when ClickHouse is running:

| Feature                  | How It Works                                               |
| ------------------------ | ---------------------------------------------------------- |
| **Table Store**          | Registers `table_store:clickhouse` capability             |
| **Query Engine**        | Registers `query_engine:clickhouse` capability            |
| **Publish Target**      | Registers `publish_target:clickhouse` capability          |
| **CLI Commands**        | `phlo clickhouse query` and `phlo clickhouse status`     |

### Default Databases

The `clickhouse-setup` init container creates four databases matching the medallion architecture:

| Database  | Purpose                                    |
| --------- | ------------------------------------------ |
| `raw`     | Raw ingestion tables (DLT landing zone)   |
| `staging` | Intermediate/staging tables               |
| `curated` | Cleaned, validated, quality-checked tables |
| `marts`   | Published analytical marts for consumption |

## Usage

### Starting ClickHouse

```bash
phlo services start --service clickhouse
```

### Running Queries

```bash
phlo clickhouse query "SELECT version()"
phlo clickhouse query --file query.sql
```

### Checking Status

```bash
phlo clickhouse status
```

### Resource Usage

```python
from phlo_clickhouse.resource import ClickHouseResource

ch = ClickHouseResource()
ch.wait_ready()
result = ch.execute("SELECT * FROM raw.mytable LIMIT 10")
```

## dbt Integration

Install with dbt support:

```bash
pip install phlo-clickhouse[dbt]
```

This provides the `dbt-clickhouse` adapter for running dbt transforms against ClickHouse.

Example dbt model config:

```sql
{{ config(
  materialized='table',
  engine='MergeTree()',
  order_by='(id, updated_at)',
) }}
```

## Port Conflict Note

`phlo-clickhouse` uses native port 19000 by default to avoid conflict with `phlo-clickstack` (which uses 9000). If you need to run both, you may need to remap one service's port.

## Entry Points

| Entry Point              | Plugin                  |
| ------------------------ | ----------------------- |
| `phlo.plugins.services` | `ClickHouseServicePlugin`, `ClickHouseSetupServicePlugin` |
| `phlo.plugins.resources` | `ClickHouseResourceProvider` |
| `phlo.plugins.cli`      | `ClickHouseCliPlugin` |

## Related Packages

- [phlo-dlt](phlo-dlt.md) - Data ingestion
- [phlo-dbt](phlo-dbt.md) - Transforms
- [phlo-clickstack](phlo-clickstack.md) - Observability (separate ClickHouse)
- [phlo-iceberg](phlo-iceberg.md) - Alternative table store

## Next Steps

- [Architecture Reference](../reference/architecture.md) - System design
- [Core Concepts](../getting-started/core-concepts.md) - Understand patterns
- [Integration Profiles](../guides/integration-profiles.md) - Profile configuration
