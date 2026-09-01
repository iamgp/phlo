# Metrics

A user reads pipeline/asset metric summaries from the in-process collector and can export them. Group `phlo metrics`. Empty collector is a valid CLI-only observation (zeros).

## Sub-features

- `summary` — `--period` default `24h` (also `7d` / `2w`); `--json` envelope with `period`, `period_hours`, `metrics`.
- `asset` — `asset NAME --runs --json`.
- `export` — `--format` json/csv/prometheus text; `--output`; `--period`; `--json`.

## How to get to it (user POV)

- `phlo metrics --help`
- `phlo metrics summary --json`
- `phlo metrics asset dlt_events --json`
- `phlo metrics export --format json`

## Driving it with CLI

Preconditions:

- Launch complete. Any cwd. Live run counts need prior materializations (often **Docker**).

- Summary JSON: `uv run --locked phlo metrics summary --json` → exit 0; envelope `data.metrics` includes `total_runs_24h`, `successful_runs_24h`, `active_assets_count` (0 on a cold collector).
- Human summary: panel titled `Metrics Summary`.
- Unknown period suffix: parser falls back per implementation; pin `--period 24h` in proofs.

## Gotchas

- This is not Prometheus scrape (`/metrics` on phlo-api). Export `--format` prometheus is a text dump of the collector.
- Asset metrics for unknown names still need a collector call; record actual stdout rather than assuming an error.
