# Doctor

A user can diagnose the local environment and project without changing it. `phlo doctor` runs grouped probes (Python, uv, container backend, disk, project config, plugins, ports, live services) and prints a table or JSON. Exit 1 if any probe is `fail`.

## Sub-features

- `doctor-table` — human `Phlo Doctor` report with per-group `ok`/`warn`/`fail`/`skip` lines and a Summary.
- `doctor-json` — `--json` object with `summary` counts and `checks[]` (`id`, `group`, `status`, `message`).
- `doctor-verbose` — `--verbose` adds exception `details` on probe failures.

## How to get to it (user POV)

- `phlo doctor`
- `phlo doctor --json`
- `phlo doctor --verbose`
- From any cwd; project-aware probes look for `phlo.yaml` / `.phlo/` in the current directory.

## Driving it with CLI

Preconditions:

- Launch complete. Cwd is either repo root or an isolated initialized project.
- Read-only: doctor must not create `.phlo/` or start containers.

- Human report: `uv run --locked phlo doctor` → stdout starts with `Phlo Doctor`; includes `Summary:` with ok/warnings/failures/skipped; exit 0 if no failures, else 1.
- JSON: `uv run --locked phlo doctor --json` → stdout starts with `{`; `checks` includes `id` `env.python` (message like `Python 3.12.x`) and `env.uv`; `doctor.bootstrap` is `ok`.
- CLI-only machine: expect `fail` on `env.docker.cli` (or compose) when Docker is missing; that is the environment, not a broken `phlo` binary. Record the JSON and continue with CLI-only features.

## Gotchas

- Exit 1 is a diagnostic result, not a crash. Parse JSON before retrying install.
- Doctor silences probe stdout so `--json` stays parseable.
- Product doctor ≠ this skill's Doctor section; still run the product command as evidence.
- Live service health checks need a generated stack; without `.phlo/` those probes skip or fail closed depending on id—record the payload, do not invent Kubernetes checks.
