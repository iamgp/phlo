# Lineage

A user inspects asset lineage (graph, impact, column lineage, export). Workspace plugin `lineage` registers `phlo lineage`.

## Sub-features

- `lineage-show` — `show ASSET --direction upstream|downstream|both --depth`
- `lineage-export` — `export ASSET --format --output`
- `lineage-impact` — `impact ASSET`
- `lineage-status` — `status`
- `lineage-column` — `column upstream|downstream ASSET --column`; `column import-dbt --manifest`

## How to get to it (user POV)

- `phlo lineage --help`
- `phlo lineage show dlt_events --direction both`
- `phlo lineage export dlt_events --format mermaid`
- `phlo lineage column upstream dlt_events --column event_id`

## Driving it with CLI

Preconditions:

- Lineage store / API typically needs generated Postgres and prior runs (**Docker**). Help and import-dbt against a file can be attempted CLI-only.

- Help: `uv run --locked phlo lineage --help` → `column`, `export`, `impact`, `show`, `status`.
- Live show without a store: capture the error. Do not invent a graph.

## Gotchas

- dbt column import needs a dbt `manifest.json` path that exists.
- Observatory lineage views are a different surface ([observatory.md](observatory.md)).
