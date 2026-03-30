# phlo-lineage (/docs/packages/phlo-lineage)



Overview [#overview]

`phlo-lineage` tracks data lineage at the row level, enabling you to trace individual records back through transformations to their source. It integrates with DLT and dbt pipelines.

Installation [#installation]

```bash
pip install phlo-lineage
# or
phlo plugin install lineage
```

Configuration [#configuration]

| Variable         | Default | Description                      |
| ---------------- | ------- | -------------------------------- |
| `LINEAGE_DB_URL` | -       | PostgreSQL DSN for lineage store |

The lineage database URL is resolved from the first available source:

1. `LINEAGE_DB_URL` (primary)
2. `PHLO_LINEAGE_DB_URL` (fallback)
3. `DAGSTER_PG_DB_CONNECTION_STRING` (tertiary - reuses Dagster's database)

Features [#features]

Auto-Configuration [#auto-configuration]

Auto-wired when `LINEAGE_DB_URL` is set:

| Feature               | How It Works                                                  |
| --------------------- | ------------------------------------------------------------- |
| **Hook Registration** | Receives `lineage.edges` events via HookBus                   |
| **Event Capture**     | Automatically captures lineage from `@phlo_ingestion` and dbt |
| **Row ID Injection**  | `_phlo_row_id` column auto-injected during ingestion          |

> **Note:** If `LINEAGE_DB_URL` is not configured, lineage events are logged but not persisted.

Event Flow [#event-flow]

```
Ingestion/Transform → emit lineage.edges → LineageHookPlugin → PostgreSQL
```

Row-Level Tracking [#row-level-tracking]

Each row gets a unique `_phlo_row_id` that allows tracing:

```sql
-- Find the source of a specific row
SELECT * FROM lineage.edges
WHERE target_row_id = 'abc123';

-- Trace full lineage chain
WITH RECURSIVE chain AS (
    SELECT * FROM lineage.edges WHERE target_row_id = 'abc123'
    UNION ALL
    SELECT e.* FROM lineage.edges e
    JOIN chain c ON e.target_row_id = c.source_row_id
)
SELECT * FROM chain;
```

Usage [#usage]

CLI Commands [#cli-commands]

```bash
# Query lineage for a table
phlo lineage show bronze.users

# Show upstream dependencies
phlo lineage show bronze.users --upstream

# Show downstream consumers
phlo lineage show bronze.users --downstream

# Export lineage graph
phlo lineage export --format json > lineage.json
phlo lineage export --format dot > lineage.dot
```

Programmatic [#programmatic]

```python
from phlo_lineage import get_lineage

# Get upstream lineage for a table
upstream = get_lineage("gold.fct_orders", direction="upstream")

# Get downstream lineage
downstream = get_lineage("bronze.raw_events", direction="downstream")

# Get full lineage graph
graph = get_lineage("silver.users", direction="both", depth=3)
```

Viewing in Observatory [#viewing-in-observatory]

The Observatory UI provides visual lineage graphs:

1. Navigate to a table in Data Explorer
2. Click the "Lineage" tab
3. Use the graph to explore dependencies

Entry Points [#entry-points]

| Entry Point          | Plugin                                |
| -------------------- | ------------------------------------- |
| `phlo.plugins.cli`   | `lineage` CLI commands                |
| `phlo.plugins.hooks` | `LineageHookPlugin` for event capture |

Related Packages [#related-packages]

* [phlo-observatory](phlo-observatory.md) - Lineage visualization
* [phlo-dlt](phlo-dlt.md) - Ingestion lineage
* [phlo-dbt](phlo-dbt.md) - Transformation lineage
* [phlo-openmetadata](phlo-openmetadata.md) - Catalog integration

Next Steps [#next-steps]

* [Architecture Reference](../reference/architecture.md) - System design
* [Developer Guide](../guides/developer-guide.md) - Building pipelines
