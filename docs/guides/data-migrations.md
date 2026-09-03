# Data Migrations

Use `phlo migrate` for table-to-table, query-to-table, or file-to-table data
backfills and reshapes defined in YAML specs.

## Workflow

1. Write a migration spec file.
2. Validate it (`phlo migrate validate`).
3. Run it in dry-run mode (`phlo migrate run --dry-run`).
4. Execute it (`phlo migrate run`).
5. Review history (`phlo migrate status`).

## Spec format

```yaml
name: backfill_orders_2025q1
version: "1.0"
description: Backfill Q1 orders from staged CSV into Iceberg table

source:
  type: csv
  path: data/orders_2025q1.csv

destination:
  table: warehouse.orders
  write_mode: merge
  unique_key: order_id

options:
  chunk_size: 50000
  parallelism: 1
  validate: true
  dry_run: false

column_mapping:
  id: order_id
  customerId: customer_id
```

## Commands

```bash
# Validate a spec file
phlo migrate validate migrations/backfill_orders_2025q1.yaml

# Execute without writes
phlo migrate run migrations/backfill_orders_2025q1.yaml --dry-run

# Execute with writes
phlo migrate run migrations/backfill_orders_2025q1.yaml

# List discoverable spec files
phlo migrate list

# Show recent migration history
phlo migrate status --limit 20
```

## Write modes

- `append`: append all rows.
- `overwrite`: replace destination contents (requires table-store overwrite support).
- `merge`: upsert semantics, requires `destination.unique_key`.

## Source adapters

`source.type` is resolved through source adapters. Keep source-specific connection
or query parameters in `source` and adapter options.

## Related

- [CLI Reference](../reference/cli-reference.md)
- [Operations Testing](../operations/testing.md)
