# Governance

A user checks and exports governance readiness from Phlo declarations (`phlo.flow` / `phlo.governance`). Group `phlo governance`. Empty declarations can pass.

## Sub-features

- `check` — `--json`; `--module` repeatable (import paths or `.py` files). Exit 1 when `ok` is false. Human: `Governance check passed` / `Governance check failed`.
- `export` — `--json` read model (`tables[]` with `table`, `owner`, `published`); human `table: owner=… published=…`.

## How to get to it (user POV)

- `phlo governance --help`
- `phlo governance check --json`
- `phlo governance check --module workflows.ingestion.csv.events`
- `phlo governance export --json`

## Driving it with CLI

Preconditions:

- Launch complete. Optional `--module` from an isolated project (csv-batch).

- JSON check from repo: `uv run --locked phlo governance check --json` → exit 0; `{"ok": true, "warning_count": 0, "warnings": []}` when nothing is declared.
- Failed check: stdout JSON `ok: false` and exit 1 (CI gate).

## Gotchas

- `--module` imports user code; only point it at `/tmp/phlo-verify-*` or the isolated project.
- This is declaration readiness, not Observatory governance UI.
