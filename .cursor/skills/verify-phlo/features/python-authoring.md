# Python authoring

A user registers lakehouse assets in project Python (under `workflows/`), not via a CLI group. Decorators are the authoring surface; CLI (`workflow`, `schema`, `materialize`) operates on those files.

## Sub-features

- `ingestion` — `@phlo.ingestion(...)` is the DLT-compatible alias (`phlo.ingestion` is callable). Preferred: `phlo.ingest.dlt(...)` or `phlo.ingest.provider("dlt")`. Also `phlo.ingest.sling(...)`. `phlo.ingest.providers()` lists installed provider names.
- `quality` — `@phlo.quality.phlo_quality(schema=…)` / `phlo_quality`; check classes `NullCheck`, `RangeCheck`, `FreshnessCheck`, …; rule helpers `not_null`, `unique`, `freshness`, `range_between`, `accepted_values`.
- `transform` — `@phlo.transform.sql(table=…, depends_on=…)` registers a SQL transform asset (`kinds` include `sql`/`transform`).
- `flow` — `phlo.publish`, `phlo.observe`, `phlo.backfill`, `phlo.contract`, `phlo.access`, `phlo.schedule` from `phlo.flow`.

## How to get to it (user POV)

- Edit `workflows/ingestion/…/*.py` and `workflows/schemas/*.py` after `phlo init --template csv-batch`.
- csv-batch writes `@phlo.ingestion(table_name="events", unique_key="event_id", validation_schema=EventsSchema, group="csv", freshness_hours=(1, 24))` on `csv_events(partition_date: str)`.
- Check with `phlo workflow check` / `phlo validate-workflow`; run with `phlo materialize` (stack).

## Driving it with CLI

Preconditions:

- Isolated csv-batch (or authored) project. Importing modules needs project deps (`phlo-dlt`, `phlo-pandera`).

- Prove files, not a hidden test API: after init, `workflows/ingestion/csv/events.py` contains `@phlo.ingestion(` and `import phlo`; `workflows/schemas/csv.py` defines `EventsSchema`.
- Optional: from the project, `uv run --locked python -c "import phlo.ingest; print(phlo.ingest.providers())"` using the workspace interpreter → includes `dlt` when `phlo-dlt` is installed.
- `phlo migrate decorators-2026-05 workflows --check` stays exit 0 on current csv-batch names.

## Gotchas

- `@phlo.ingestion` is compatibility; new code should use `phlo.ingest.dlt`.
- `get_ingestion_assets` / `get_quality_checks` are Python APIs, not CLI.
- SQL transform captures SQL by calling `fn()` at decorate time; required parameters → SQL stored as unavailable.
- Missing provider: `ModuleNotFoundError` `Ingestion provider 'name' is not installed`.
