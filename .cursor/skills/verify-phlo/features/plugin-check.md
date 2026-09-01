# Plugin lifecycle

A user can list, inspect, validate, search, install, update, and scaffold Phlo plugins. `phlo plugin` is a core group (`src/phlo/cli/commands/plugin`). Check is the usual health gate; `--containers` is a separate Docker-backed scan of generated Dockerfiles.

## Sub-features

- `plugin-list` — `list --json` has `installed`; `--all` adds `available`.
- `plugin-info` — `info NAME --json` (type auto-detected; `--type` optional).
- `plugin-check` — interface validation; JSON keys `valid` / `invalid`.
- `plugin-check-containers` — **Docker required.** `--remote-images` requires `--containers`.
- `plugin-search` — `search QUERY --json` (installed + registry).
- `plugin-install` — `install NAME` (mutation; registry pin).
- `plugin-update` — `update --dry-run` / `--json` is read-only; applying updates is a mutation.
- `plugin-create` — `create NAME --type source|quality|… --json` writes a package scaffold.

## How to get to it (user POV)

- `phlo plugin --help`
- `phlo plugin list` / `--type cli` / `--json` / `--all`
- `phlo plugin info dagster --json`
- `phlo plugin check` / `--json` / `--containers`
- `phlo plugin search trino --json`
- `phlo plugin install phlo-trino` (not for this checkout’s workspace members)
- `phlo plugin update --dry-run`
- `phlo plugin create my-source --path /tmp/…`

## Driving it with CLI

Preconditions:

- Launch complete from repo root so workspace providers are on the entry-point path.
- For `--containers`: Docker CLI + Compose, daemon reachable.
- Drive create/install only in `/tmp/phlo-verify-$RUN_ID`, never this repo.

- List CLI plugins: `uv run --locked phlo plugin list --type cli --json` → exit 0; `installed` names in this workspace include `alerts`, `clickhouse`, `clickstack`, `dagster`, `dbt`, `dlt`, `hasura`, `lineage`, `mcp`, `minio`, `nessie`, `openmetadata`, `postgres`, `postgrest`, `quality`, `sling`, `trino` (17).
- Info: `uv run --locked phlo plugin info dagster --json` → exit 0; `name` is `dagster`; description mentions materialize/backfill.
- Validate: `uv run --locked phlo plugin check --json` → exit 0; `invalid` is `[]`; `valid` is a non-empty list (76 on a full workspace sync). Human mode ends with `All plugins are valid!`.
- Dry update: `uv run --locked phlo plugin update --dry-run` → lists updates or none; does not pip-install.
- Containers (**Docker**): `uv run --locked phlo plugin check --containers` → generated Dockerfile checks. `--remote-images` without `--containers` → UsageError.

## Gotchas

- `plugin check --json` is raw `{valid, invalid}`, not the init envelope. `create`/`install` `--json` use the envelope.
- `--type` CLI aliases: `cli` maps to `cli_command`.
- Search/install hit the plugin registry over the network.
- `--containers` builds a **temporary** user project internally; not your `/tmp/phlo-verify-*`.
- `phlo doctor` still loads if a plugin is broken; most other commands do not.
