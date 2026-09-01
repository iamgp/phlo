# Project tests

A user runs pytest for a Phlo **project** (workflows under `tests/`), not the framework suite. `phlo test` shells out to `pytest`, preferring `uv run pytest` when `uv` and `pyproject.toml` exist.

## Sub-features

- `test-all` — `phlo test` (all tests).
- `test-asset` — `phlo test ASSET` looks for `tests/test_ASSET.py`.
- `test-local` — `--local` sets `PHLO_TEST_LOCAL=1` and adds `-m not integration` (or `(marker) and not integration`).
- `test-coverage` / `test-verbose` / `test-marker` — `--coverage`, `-v`, `-m MARKER`.

## How to get to it (user POV)

- From a generated project after `uv pip install -e .`: `phlo test`, `phlo test --local`, `phlo test --coverage`, `phlo test -m integration`.
- csv-batch next steps include `phlo test`.

## Driving it with CLI

Preconditions:

- Cwd is an isolated project with `tests/`. Framework checkout `make test` is a different path (`uv run --locked pytest`).
- `--local` is the CLI-only slice. Integration markers expect Docker/services.

- Missing tests dir / no matches: pytest returncode 5 with no `ASSET` → CLI prints `No tests were collected. Add tests under tests/ to enable this gate.` and exits **0**.
- Missing asset file: `phlo test missing_asset` → stderr `Test file not found: tests/test_missing_asset.py`, exit 1.
- Local: `phlo test --local` → stdout includes `Local test mode enabled (PHLO_TEST_LOCAL=1)`.

## Gotchas

- This is not `make test` / `pytest -m 'not integration'` in the Phlo repo.
- `--local` skips integration tests; do not mark slow unit tests as integration in product projects either (house bar).
- Requires `pytest` installed in the project env; else `pytest not found`.
