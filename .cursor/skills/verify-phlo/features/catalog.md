# Catalog and branches

A user lists lakehouse tables and manages Nessie branches. Workspace plugin `nessie` registers `catalog` and `branch`.

## Sub-features

- `catalog-tables` — `catalog tables --namespace --ref --format`
- `catalog-describe` — `catalog describe TABLE --ref`
- `catalog-history` — `catalog history TABLE --limit --ref --format`
- `branch-list` — `branch list --all --format`
- `branch-create` / `delete` / `diff` / `merge` — `create NAME --from`; `delete NAME --force`; `diff SRC DST --format`; `merge SRC DST --dry-run --no-delete-source`

## How to get to it (user POV)

- After stack + materialize: `phlo catalog tables` (README quickstart).
- `phlo catalog describe events`
- `phlo branch list`
- `phlo branch create explore --from main`

## Driving it with CLI

Preconditions:

- Nessie (and usually Trino/Iceberg) running via `phlo services start` (**Docker**).
- Isolated project cwd.

- Help: `uv run --locked phlo catalog --help` → `describe`, `history`, `tables`.
- Help: `uv run --locked phlo branch --help` → `create`, `delete`, `diff`, `list`, `merge`.
- Live `tables` without Nessie fails with a connection/backend error; record it. Do not claim tables exist on a Docker-less VM.

## Gotchas

- Merge/delete are mutations. Prefer `--dry-run` on merge first.
- Catalog is Nessie-backed, not OpenMetadata (`phlo openmetadata`).
