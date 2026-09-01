# Serving APIs

A user manages Hasura metadata and PostgREST helpers against running services. Workspace plugins `hasura` and `postgrest`. **Docker** for anything that talks to the API.

## Sub-features

- `hasura-status` / `track` / `relationships` / `permissions` / `auto-setup` / `export` / `apply` / `sync-permissions` — `--schema -v`; export `--output`; apply `--input`.
- `postgrest-generate-views` — `--output --apply --diff --models --schema`
- `postgrest-reload-schema`
- `postgrest-setup-auth` — `--host --port --database --user --password --force -q`

## How to get to it (user POV)

- After `phlo services init --profile api` and start:
  - `phlo hasura status`
  - `phlo hasura track --schema public`
  - `phlo postgrest reload-schema`

## Driving it with CLI

Preconditions:

- API profile services running (**Docker**). Help is CLI-only.

- Help: `uv run --locked phlo hasura --help` → `apply`, `auto-setup`, `export`, `permissions`, `relationships`, `status`, `sync-permissions`, `track`.
- Help: `uv run --locked phlo postgrest --help` → `generate-views`, `reload-schema`, `setup-auth`.
- Live track/reload: only with running Hasura/PostgREST. Capture counts (`Tracked N/M tables`) from source help/examples.

**Not live-proven without Docker.**

## Gotchas

- Default local stack may omit api profile; `services init --profile api`.
- `apply` / `setup-auth --force` mutate metadata/db.
