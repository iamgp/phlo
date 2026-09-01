# Schema migrate

A user diffs, plans, applies, and records table schema migrations between quality schemas and storage. Group `phlo schema-migrate`. Needs a registered `SchemaMigrator` (e.g. `phlo-iceberg`) and usually a live catalog.

## Sub-features

- `diff` / `plan` / `apply` — `TABLE --schema-class --migration-file --rename`; apply has `--yes --dry-run`.
- `history` — `TABLE --limit --format`.
- `export-contract` — `TABLE --schema-class --output --force`.
- `scaffold-yaml` / `scaffold-yaml-recent` — YAML from contract or recent changes (`--since-hours`, `--limit`, `--force`).

## How to get to it (user POV)

- `phlo schema-migrate --help`
- After tables exist: `phlo schema-migrate diff events --schema-class workflows.schemas.csv.EventsSchema`
- `phlo schema-migrate plan …` then `apply … --dry-run` then `apply … --yes`

## Driving it with CLI

Preconditions:

- Isolated project with quality schema classes and a table store. Iceberg migrator installed in this workspace.
- Live apply/history typically need **Docker** stack (Nessie/Iceberg/Trino). Dry-run/plan may still fail without catalog connectivity—record the error, do not fake success.

- Help: `uv run --locked phlo schema-migrate --help` → Commands `apply`, `diff`, `export-contract`, `history`, `plan`, `scaffold-yaml`, `scaffold-yaml-recent`.
- No migrator: prints `No schema migrator registered.` and exit 1.
- Apply is a mutation (`require_mutation_authorization`). `--dry-run` on apply must skip writes; observe that no table change occurs.

## Gotchas

- Not `phlo migrate` (data specs / decorator codemod) and not `phlo schema` (Pandera files).
- Configured `schema_migrator` / `table_store` in `phlo.yaml` capabilities must match an installed provider.
