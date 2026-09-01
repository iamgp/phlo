# Config

A user shows, validates, and upgrades `phlo.yaml` infrastructure configuration.

## Sub-features

- `config-show` — effective config; `--format yaml|json` (default yaml). JSON is `{"infrastructure": …}`.
- `config-validate` — parse `phlo.yaml` (`infrastructure`, `api`, `services` overrides). Exit 1 if file missing or invalid.
- `config-upgrade` — `--force` writes/updates infrastructure section.

## How to get to it (user POV)

- From a project: `phlo config show`, `phlo config show --format json`, `phlo config validate`, `phlo config upgrade`.

## Driving it with CLI

Preconditions:

- Isolated project with `phlo.yaml` from `phlo init`. Repo root of this checkout has **no** `phlo.yaml`.

- Missing file: from repo root, `uv run --locked phlo config validate` → `Warning: No phlo.yaml found in current directory` and `Run phlo services init to create infrastructure configuration`, exit 1.
- After init: `uv run --locked phlo config validate` in the project → table of checks, exit 0. Missing `infrastructure` key prints a warning and suggests `phlo config upgrade`.
- Show JSON: `uv run --locked phlo config show --format json` → parseable `infrastructure` object, exit 0.

## Gotchas

- Validate looks at cwd `phlo.yaml` only.
- Upgrade mutates the file; use `--force` only in `/tmp/phlo-verify-*`.
