# dbt

A user compiles, runs, and tests dbt projects and can scaffold a publishing layer. Workspace plugin `dbt` registers `phlo dbt` (`compile`, `run`, `test`, `publishing`).

## Sub-features

- `dbt-compile` — `dbt compile --target --local`
- `dbt-run` — `dbt run --target --select --local` (mutation / container)
- `dbt-test` — `dbt test --target --select --local`
- `dbt-publishing-scaffold` — `dbt publishing scaffold --manifest --output --select … --dry-run`

## How to get to it (user POV)

- After `phlo init --template basic` or `dbt-medallion`: `phlo dbt compile`
- `phlo dbt run --select stg_events`
- `phlo dbt test`
- `phlo dbt publishing scaffold --manifest transforms/…/manifest.json --dry-run`

## Driving it with CLI

Preconditions:

- dbt project under `workflows/**/transforms/dbt` or `DBT_PROJECT_DIR`.
- Default execution is **inside the orchestrator container** when `.phlo/` exists (**Docker**). `--local` runs host `dbt` if installed.
- Missing project: CLI error text from `DBT_PROJECT_HELP` (`Create or copy a dbt project under workflows/…`).

- Help: `uv run --locked phlo dbt --help` → `compile`, `publishing`, `run`, `test`.
- Local compile without Docker: `phlo dbt compile --local` from a dbt-ready project; capture compile success or missing dbt binary (`dbt command not found`).
- Publishing `--dry-run` must not write `--output`.

## Gotchas

- csv-batch is not dbt-ready; use `basic` / `dbt-medallion`.
- Container path maps project files under `/app/…`.
- Run/test are mutations when they execute.
