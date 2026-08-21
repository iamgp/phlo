# Retail Files

Deterministic external-consumer example for Phlo 0.14.0. `uv sync --group dev`
creates the only runtime environment; it pins packaged `phlo`, `phlo-dlt`, and
`phlo-pandera` 0.14.0. Generated data is deliberately uncommitted.

```bash
uv sync --group dev
uv run python scripts/generate_fixtures.py --scale test
uv run pytest -q tests
# representative default: 25 stores × 30 days × 80 lines = 60,000 CSV sales rows
uv run python scripts/generate_fixtures.py --scale default
uv run python scripts/materialize.py
uv run dbt run --project-dir workflows/transforms/dbt --profiles-dir workflows/transforms/dbt/profiles
uv run dbt test --project-dir workflows/transforms/dbt --profiles-dir workflows/transforms/dbt/profiles
```

The direct materializer/dbt commands are local DuckDB diagnostics, not a claimed
Iceberg/Nessie/Trino/Dagster execution. `phlo.yaml` and the decorated ingestion
assets are included for discovery, but a live Phlo service profile is not supplied
by this example or validated in this orb.

Sources: per-store/per-day CSV sales, JSON product/store/promotion references,
NDJSON inventory snapshots, and a Parquet historical archive. Missing one store
file fails completeness. Contracts enforce line uniqueness, accepted values,
return signs, arithmetic, reference keys, and inventory constraints. dbt builds
sales facts, product/store dimensions, inventory balances, daily store marts,
product-category performance, and stockout/reorder outputs.
