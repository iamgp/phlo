# Contracts

A user snapshots table JSON schemas into the schema registry and checks compatibility. Group `phlo contracts`.

## Sub-features

- `snapshot` — `--table` (required) `--schema-file` (required JSON) `--run-id` `--source` (default `cli`). Mutation.
- `check` — `--table` `--fail-on` compatibility threshold.

## How to get to it (user POV)

- `phlo contracts --help`
- `phlo contracts snapshot --table db.schema.events --schema-file contract.json`
- `phlo contracts check --table db.schema.events --fail-on …`

## Driving it with CLI

Preconditions:

- Registry DSN: `PHLO_REGISTRY_DB_URL` or `PHLO_LINEAGE_DB_URL` or `DAGSTER_PG_DB_CONNECTION_STRING`. Without it: `No registry database URL configured.` exit 1.
- That database is typically the generated Postgres (**Docker**). Do not claim snapshot success without the DSN.

- Help: `uv run --locked phlo contracts --help` → Commands `check`, `snapshot`.
- Missing DSN from repo cwd: `uv run --locked phlo contracts snapshot --table t --schema-file /dev/null` → fails on missing URL or unreadable schema; record the exact message.

## Gotchas

- Not `phlo schema-migrate export-contract` (Iceberg contract YAML) and not Observatory contract UI.
- Snapshot is authorization-gated.
