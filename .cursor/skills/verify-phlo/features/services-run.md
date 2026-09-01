# Services run

A user starts, inspects, logs, execs, restarts, resets, and stops the generated Compose project. These commands require a container backend (Docker Compose v2 per README; Podman is experimental). Root `phlo logs` is the same infrastructure logs command as `phlo services logs` (core registers `logs` before plugins, so Dagster `logs` is skipped).

## Sub-features

- `services-start` — **Docker.** `-d/--detach`, `--build`, `--profile`, `--service`, `--native`, `--backend`.
- `services-status` — **Docker.** `--json`, `--service`, `--backend`. Missing compose → “Phlo services have not been initialized”.
- `services-stop` — **Docker.** `-v/--volumes`, `--native`, `--profile`, `--service`.
- `services-restart` / `services-reset` — **Docker.** reset: `--yes/-y`, `--service`.
- `services-logs` / `phlo logs` — **Docker.** `-f/--follow`, `-n/--tail`, `--since`, `--until`.
- `services-exec` — **Docker.** `exec SERVICE COMMAND --tty --backend`.

## How to get to it (user POV)

- After [services-generate.md](services-generate.md) in the project cwd:
  - `phlo services start`
  - `phlo services status` / `--json`
  - `phlo logs` or `phlo services logs -f`
  - `phlo services exec postgres -- psql …` (postgres plugin exists separately)
  - `phlo services stop`
  - `phlo services reset --yes` (destroys volumes)

## Driving it with CLI

Preconditions:

- Isolated project with `.phlo/docker-compose.yml` from `phlo services init --no-dev`.
- Docker daemon + Compose v2. **If `phlo doctor --json` has `env.docker.cli` fail, do not claim this feature was proven.**
- One live stack per machine (host ports collide).

- Start: `uv run --locked phlo services start` from the project cwd → exit 0 after readiness (generated healthchecks; start path uses ~60s timeout).
- Status: `uv run --locked phlo services status --json` → exit 0; JSON of compose `ps`; not `No services running or error checking status.`
- Logs: `uv run --locked phlo logs --tail 20` → compose log lines, exit 0.
- Stop: `uv run --locked phlo services stop` → only this compose project.

This VM’s default proof does **not** run start; document the path only unless Docker is actually up.

## Gotchas

- `phlo status` is **Dagster asset status**, not service status. Service status is `phlo services status`.
- `phlo logs` is infrastructure logs, not Dagster run logs (plugin `logs` skipped).
- Never `killall docker` / pkill by name. Stop the project you started.
- `--native` is a subprocess mode, not Compose; do not mix with unverified assumptions.
