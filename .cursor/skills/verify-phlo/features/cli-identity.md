# CLI identity

A user can ask the installed `phlo` binary who it is and which commands exist. `--version` prints the packaged version; `--help` lists the root command groups without requiring a project directory or a running stack.

## Sub-features

- `version` — print `phlo, version 0.14.0` and exit 0.
- `help` — print usage including core groups from `src/phlo/cli/main.py` and discovered plugin commands.
- `quiet-nocolor` — global `--quiet` and `--no-color` flags are accepted on the root group.

## How to get to it (user POV)

- Shell: `phlo --version` or `phlo --help` after `uv sync --locked` (or `uv pip install "phlo[defaults]"` outside this checkout).
- Same commands via `uv run --locked phlo …` from the Phlo repo root.
- No project cwd required.

## Driving it with CLI

Preconditions:

- Launch complete (`uv sync --locked`); `uv run --locked phlo` resolves this workspace.
- Any cwd is fine; prefer repo root so the locked env is used.

- Ask for the version: `uv run --locked phlo --version` → stdout is `phlo, version 0.14.0`, exit 0.
- Ask for root help: `uv run --locked phlo --help` → stdout Usage line `phlo [OPTIONS] COMMAND [ARGS]...`; **core** Commands include `init`, `doctor`, `support`, `test`, `audit`, `logs`, `services`, `workflow`, `plugin`, `schema-migrate`, `migrate`, `metrics`, `contracts`, `config`, `env`, `authz`, `compliance`, `governance`.
- With workspace plugins installed, the same `--help` also lists plugin roots: `alerts`, `backfill`, `branch`, `catalog`, `clickhouse`, `clickstack`, `dbt`, `dev`, `hasura`, `lineage`, `materialize`, `mcp`, `minio`, `openmetadata`, `postgres`, `postgrest`, `schema`, `sling`, `status`, `trino`, `validate-schema`, `validate-workflow`.
- Confirm the console script: `uv run --locked python -c "from importlib.metadata import version; print(version('phlo'))"` → `0.14.0`.

## Gotchas

- A global `phlo` on PATH may be a different install; always use `uv run --locked` in this repo.
- Plugin command names that collide with core are **skipped** (`cli.add_command` only if `command.name not in cli.commands`). In this tree, core `logs` wins over Dagster `logs`; core `workflow` wins over dlt `workflow`.
- Alpha: extra provider packages change the help list; do not invent names that `--help` does not print.
- `--help` on a subcommand is a different entry; this feature is the root group plus `--version`.
