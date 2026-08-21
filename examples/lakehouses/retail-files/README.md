# Retail Files lakehouse

This self-contained Phlo 0.14.0 example ingests a small, deterministic retail
drop without network access. It is intentionally the first, file-oriented example
in the lakehouse suite: it does not require Phlo services, credentials, or an
object store.

## Layout

* `data/` contains CSV sales, JSON products, NDJSON inventory, and a generated
  Parquet historical-sales archive.
* `workflows/ingestion/retail/` declares the three Phlo ingestion assets and
  reads the local files.
* `workflows/schemas/retail.py` contains Pandera contracts.
* `workflows/quality/retail.py` contains the business checks used by the local
  materializer.
* `workflows/transforms/dbt/` is a dbt-duckdb project producing `sales_facts`,
  `product_dimension`, `inventory_balances`, and `daily_store_mart`.

## Setup and materialization

Use this project's isolated environment. In normal release use, `uv sync` resolves
the pinned 0.14.0 packages from the package index; no repository source path or
editable dependency is used.

```bash
cd examples/lakehouses/retail-files
uv sync --group dev
uv run python scripts/generate_fixtures.py
uv run python scripts/materialize.py --partition 2025-01-15
uv run pytest -q tests
uv run dbt compile --project-dir workflows/transforms/dbt --profiles-dir workflows/transforms/dbt/profiles
uv run dbt run --project-dir workflows/transforms/dbt --profiles-dir workflows/transforms/dbt/profiles
uv run dbt test --project-dir workflows/transforms/dbt --profiles-dir workflows/transforms/dbt/profiles
```

During the 0.14.0 release window, build non-editable wheels for `phlo`,
`phlo-dlt`, and `phlo-pandera`, then install those wheel files into this same
project-local `.venv`. This is only a release-state validation procedure; do not
add repository paths or editable dependencies to this project.

`materialize.py` writes `retail.duckdb`, replaces only the requested sales
partition, and runs contracts plus duplicate, product-reference, and revenue
reconciliation checks before dbt runs. Re-run the same partition command to
exercise replay/idempotency; the fact count and total remain unchanged.

For a Phlo-orchestrated deployment, the asset declarations are in
`workflows/ingestion/retail/`; the local materializer is deliberately the cheapest
network-free executable path for this example.

## Expected outputs

The normal `2025-01-15` drop produces two sales facts, two product-dimension
rows, two latest inventory balances, and one daily-store-mart row with revenue
`47.00`. The historical Parquet archive adds one prior-day fact.

## Intentional failures

`data/failures/` is excluded from normal runs. It includes a duplicate sales row,
malformed JSON, and malformed NDJSON. `scripts/generate_fixtures.py --missing-store
2025-01-16` demonstrates the explicit missing-sales-file error. These paths are
covered by tests and must fail rather than silently producing partial results.
