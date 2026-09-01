# Data migrate

A user validates and runs declarative data-migration specs, lists them, shows history, and can rewrite May 2026 flow decorator APIs. Group `phlo migrate`.

## Sub-features

- `migrate-list` — `list --directory` (default project migrations dir). “No migration specs found.” is exit 0.
- `migrate-validate` — `validate SPEC_FILE`.
- `migrate-run` — `run SPEC_FILE --dry-run --format` (mutation unless dry-run).
- `migrate-status` — `status --limit --format`.
- `decorators-2026-05` — `decorators-2026-05 PATH --check|--write|--diff`. `--check` and `--write` are exclusive. `--check` exits 1 if files still need migration.

## How to get to it (user POV)

- `phlo migrate --help`
- `phlo migrate list`
- `phlo migrate validate path/to/spec.yaml`
- `phlo migrate run path/to/spec.yaml --dry-run`
- `phlo migrate decorators-2026-05 workflows --check`

## Driving it with CLI

Preconditions:

- Isolated project. Spec `run` may need database connectivity (**Docker** / DSN). List/validate/codemod `--check` are CLI-only.

- List from repo or empty project: `uv run --locked phlo migrate list` → `No migration specs found.` exit 0.
- Codemod check: `uv run --locked phlo migrate decorators-2026-05 "$PROJECT/workflows" --check` → exit 0 if csv-batch already uses `@phlo.ingestion(`; exit 1 if old names remain.
- Dry-run run: `phlo migrate run spec.yaml --dry-run` → shows plan without applying; confirm no history row / no table rewrite.

## Gotchas

- `--write` on the codemod is a mutation and rewrites Python in place—only in `/tmp/phlo-verify-*`.
- History lives with the executor; empty project has no status rows.
