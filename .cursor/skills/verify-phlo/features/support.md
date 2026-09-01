# Support status

A user compares installed Phlo packages to the bundled, offline v1 support manifest. `phlo support status` needs no project and no network. Exit 0 compatible, 1 incompatible, 2 unknown (no manifest).

## Sub-features

- `support-human` — header `Phlo Support Status`, Compatible / Production ready, Packages, Gates.
- `support-json` — `--json` stable sorted object: `compatible`, `production_ready`, `gates`, `items[]` (`name`, `expected`, `installed`, `kind`, `status`).

## How to get to it (user POV)

- `phlo support --help`
- `phlo support status`
- `phlo support status --json`

## Driving it with CLI

Preconditions:

- Launch complete. Any cwd. Fast-path: `phlo support` skips heavy plugin import (see `src/phlo/cli/main.py`).

- JSON: `uv run --locked phlo support status --json` → parse object; each workspace package appears in `items`. `compatible` is boolean or null. Exit **1** when `compatible` is false (this full workspace reports extra packages as `unexpected` and exits 1 even when core items are `0.14.0`). Exit **2** only when `compatible` is null.
- Human: `uv run --locked phlo support status` → starts with `Phlo Support Status`; includes `Manifest: bundled (trusted)`.

## Gotchas

- A full `uv sync --locked` workspace installs preview packages not in the blessed set; exit 1 is then expected, not a broken CLI.
- `production_ready` is false while gates are `planned`/`blocked` (alpha).
- Do not confuse this with `phlo doctor` (environment probes).
