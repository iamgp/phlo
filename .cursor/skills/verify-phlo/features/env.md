# Env export

A user exports the generated dotenv for the selected services. `phlo env export` rebuilds env from plugin discovery + `phlo.yaml` overrides.

## Sub-features

- `env-export` — stdout dotenv (`--format dotenv` only).
- `env-output` — `--output FILE` instead of stdout.
- `env-secrets` — `--include-secrets` merges `.phlo/.env.local` real values (do not commit).

## How to get to it (user POV)

- From a project (after or instead of init): `phlo env export`
- `phlo env export --output /tmp/env.full`
- `phlo env export --include-secrets` (secrets)

## Driving it with CLI

Preconditions:

- Service plugins installed. No services → `No services found. Install service plugins or run from a Phlo project directory.`
- Isolated project cwd.

- Export: `uv run --locked phlo env export` → exit 0; stdout is KEY=VALUE lines (no secrets unless flagged).
- `--include-secrets` after `services init` includes values from `.phlo/.env.local`; evidence must not be committed if it contains passwords.

## Gotchas

- Format is dotenv only.
- This regenerates from plugins; it is not `cat .phlo/.env`.
- Never copy `--include-secrets` output into git or the skill artifacts example.
