# Materialize and asset status

A user materializes Dagster assets, backfills partitions, inspects asset status, and can start `phlo dev`. These come from workspace plugin `dagster` (`phlo-dagster` `cli_plugin.py`: commands `dev`, `logs`, `status`, `backfill`, `materialize`). Core already owns `phlo logs`, so plugin `logs` is **not** registered.

## Sub-features

- `materialize` — `ASSET` or `--select`; `-p/--partition`; `--no-default-partition`; `--no-contract-refresh`; `--dry-run` prints the command without executing.
- `backfill` — `ASSET --start-date --end-date --partitions --parallel --resume --dry-run --delay`.
- `status` — `phlo status --assets --services --group --stale --json` (asset/job status, **not** `services status`).
- `dev` — `phlo dev --host --port --workflows-path` (Dagster dev server). Needs `pyproject.toml` in cwd.

## How to get to it (user POV)

- After csv-batch + stack: `phlo materialize dlt_events --partition 2025-01-15`
- `phlo materialize dlt_events --dry-run`
- `phlo backfill dlt_events --start-date 2025-01-01 --end-date 2025-01-07 --dry-run`
- `phlo status --json`
- `phlo dev`

## Driving it with CLI

Preconditions:

- Isolated project with generated compose. Live materialize/backfill/dev talk to the container backend (**Docker**).
- CLI-only slice: `--dry-run` (no execution). Missing ASSET and `--select` → UsageError `Provide ASSET_NAME or --select.`
- Partitioned assets default `--partition` to today UTC unless `--no-default-partition`.

- Dry-run: from a project that can resolve compose, `uv run --locked phlo materialize dlt_events --partition 2025-01-15 --dry-run` → stdout contains `Dry run - would execute:` and the command; exit 0; **no** materialization. If compose/backend is missing, capture that error instead of inventing success.
- Help: `uv run --locked phlo materialize --help` lists `--dry-run`, `--partition`, `--select`.

**Not live-proven without Docker.** Do not treat dry-run as a successful warehouse write.

## Gotchas

- `phlo status` ≠ `phlo services status`.
- WAP in `phlo.yaml` forbids `--select` and requires a single ASSET_NAME.
- `phlo dev` is a long-running process; tear down only the PID you started.
