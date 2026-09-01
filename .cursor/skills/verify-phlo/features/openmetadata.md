# OpenMetadata

A user checks OpenMetadata health and syncs lakehouse metadata. Workspace plugin `openmetadata`.

## Sub-features

- `openmetadata-health` — `phlo openmetadata health`
- `openmetadata-sync` — `sync --include-namespace --exclude-namespace --dbt --dbt-schema`

## How to get to it (user POV)

- After catalog profile services: `phlo openmetadata health`
- `phlo openmetadata sync`

## Driving it with CLI

Preconditions:

- OpenMetadata stack from services catalog profile (**Docker**). Optional extra `phlo[openmetadata]`.

- Help: `uv run --locked phlo openmetadata --help` → `health`, `sync`.
- Live health: HTTP to the generated OpenMetadata service; without it, connection error.

**Not live-proven without Docker.**

## Gotchas

- Not `phlo catalog` (Nessie).
- Sync is a mutation against OpenMetadata.
