# CLI identity

A user can ask the installed `phlo` binary who it is and which commands exist. `--version` prints the packaged version; `--help` lists the root command groups without requiring a project directory or a running stack.

## Sub-features

- `version` — print `phlo, version 0.14.0` and exit 0.
- `help` — print usage including `init`, `services`, `plugin`, `doctor`, and `test`.
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
- Ask for root help: `uv run --locked phlo --help` → stdout Usage line `phlo [OPTIONS] COMMAND [ARGS]...`, Commands include `init`, `services`, `plugin`, `doctor`, `test`; exit 0.
- Confirm the console script: `uv run --locked python -c "from importlib.metadata import version; print(version('phlo'))"` → `0.14.0`.

## Gotchas

- A global `phlo` on PATH may be a different install; always use `uv run --locked` in this repo.
- Alpha: command list grows with installed provider plugins; `init` / `services` / `plugin` / `doctor` are core.
- `--help` on a subcommand (for example `phlo init --help`) is a different entry; this feature is the root group only.
