# Services generate and run

A user generates a local lakehouse stack from installed service plugins (no hand-written Compose), then can start and inspect it when Docker is available. `phlo services init` writes `.phlo/docker-compose.yml` and env files; `start` / `status` / `stop` talk to the container backend.

## Sub-features

- `services-help` — `phlo services` with no subcommand prints help listing `init`, `start`, `status`, `stop`.
- `services-init` — generate `.phlo/` runtime files from discovered plugins.
- `services-start-status` — start the generated compose project and show service state (Docker required).
- `services-stop` — stop only the stack this project started.

## How to get to it (user POV)

- After `phlo init`, from the project directory:
  - `phlo services init`
  - `phlo services start`
  - `phlo services status` / `phlo services status --json`
  - `phlo services stop`
- Optional: `phlo services init --profile observability`, `--dev`, `--no-dev`, `--force`.
- `phlo services list --json` lists discovered services even before init (runtime status may be empty without Docker).

## Driving it with CLI

Preconditions:

- Isolated project already created (`phlo init`); cwd is that project.
- Workspace `phlo` on PATH via `uv run --locked` from the **repo** (or the project env after `uv pip install -e .` plus defaults).
- `services-init` does not need a running daemon; it writes files.
- `start` / `status` require Docker + Compose v2 (README prerequisites). If the VM cannot run Docker, stop after init proof or skip this feature and prove `project-init` instead.

- Show the group: `uv run --locked phlo services --help` → Commands include `init`, `start`, `status`, `stop`; exit 0.
- Generate the stack: from the project cwd, `uv run --locked phlo services init --no-dev` → exit 0; stdout includes `Created: .phlo/docker-compose.yml`, `Created: .phlo/.env`, `Created: .phlo/.env.local`, and `Phlo infrastructure initialized.`; those three files exist. `--no-dev` avoids auto-enabling checkout mounts when the repo is detectable.
- Start (Docker only): `uv run --locked phlo services start` → wait until the command exits 0 (readiness is driven by generated healthchecks, timeout on the order of 60s per start path). Then `uv run --locked phlo services status` → exit 0; table or JSON of services, not `No services running`.
- Stop what this run started: `uv run --locked phlo services stop` from the same cwd.

## Gotchas

- Do not hand-write Compose; providers generate it. Regenerating into a non-empty `.phlo/` needs `--force`.
- Auto `--dev` can enable if a Phlo checkout is detected; use `--no-dev` in disposable verify projects unless you intend mounts.
- Host ports collide if two stacks run at once. One live stack per machine for v1 verify.
- `status` requires `.phlo/docker-compose.yml` and a container backend; without Docker it errors rather than listing files.
- `plugin check --containers` is a different path (temp project + image scanners), not a substitute for `services start`.
- Materialize / catalog / Observatory need a running stack; they are out of this feature's CLI-only slice.
