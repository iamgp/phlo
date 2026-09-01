# Services generate

A user generates a local lakehouse stack from installed service plugins without hand-writing Compose. `phlo services init` writes `.phlo/docker-compose.yml` and env files. `list` / `add` / `remove` / `ports` inspect or change the rendered set. Starting the stack is [services-run.md](services-run.md).

## Sub-features

- `services-help` — `phlo services` with no subcommand prints help.
- `services-init` — generate `.phlo/` (`--force`, `--name`, `--dev`, `--no-dev`, `--phlo-source`, `--service-dev`, `--production`, `--profile`).
- `services-list` — discovered services; `--json`; `--all`; `--backend`.
- `services-ports` — declared host/container ports (`--json`, `--all`).
- `services-add` / `services-remove` — change rendered services (`add` has `--no-start`, `--profile`).

## How to get to it (user POV)

- After `phlo init`, from the project directory: `phlo services init` (prefer `--no-dev` in disposable dirs).
- `phlo services list --json`
- `phlo services ports --json`
- `phlo services add <service> --no-start` / `phlo services remove <service>`
- Optional init: `--profile observability`, `--profile api`, `--force`, `--production`.

## Driving it with CLI

Preconditions:

- Isolated project from `phlo init`; cwd is that project when generating files.
- `uv run --locked phlo` from the **repo** (or project env after `uv pip install -e .` plus defaults).
- Init/list do **not** need a running Docker daemon; they write or discover. `ports` / `add` after init still talk to generated compose; `add` without `--no-start` will try to start (**Docker**).

- Help: `uv run --locked phlo services --help` → Commands include `add`, `exec`, `init`, `list`, `logs`, `ports`, `remove`, `reset`, `restart`, `start`, `status`, `stop`; exit 0.
- Generate: from the project cwd, `uv run --locked phlo services init --no-dev` → exit 0; stdout includes `Created: .phlo/docker-compose.yml`, `Created: .phlo/.env`, `Created: .phlo/.env.local`, and `Phlo infrastructure initialized.`; those files exist.
- List: `uv run --locked phlo services list --json` → JSON array of service objects with `name`, `default`, `disabled`, `running` (running is false without a backend).
- Live start/status: see [services-run.md](services-run.md). **Not proven on a Docker-less VM.**

## Gotchas

- Do not hand-write Compose. Re-init into a non-empty `.phlo/` needs `--force`.
- Auto `--dev` enables if a Phlo checkout is detected; use `--no-dev` unless you intend mounts.
- `add` without `--no-start` is a run mutation, not generate-only.
- Production init rejects default postgres/minio credentials.
