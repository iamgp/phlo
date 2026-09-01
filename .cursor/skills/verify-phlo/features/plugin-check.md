# Plugin check

A user can list discovered plugins and validate that installed plugins satisfy their interfaces. `phlo plugin check` reports valid vs invalid plugin ids; `--json` is parseable without prose prefixes. `--containers` is a separate, Docker-backed check of generated Dockerfiles.

## Sub-features

- `plugin-list` — list installed plugins; `--json` has `installed` (and `available` with `--all`).
- `plugin-check` — interface validation; success prints `All plugins are valid!` or JSON with empty `invalid`.
- `plugin-check-containers` — generate a temporary user project and lint/scan container files (Docker required).

## How to get to it (user POV)

- `phlo plugin --help`
- `phlo plugin list` / `phlo plugin list --json` / `phlo plugin list --type sources`
- `phlo plugin check` / `phlo plugin check --json`
- `phlo plugin check --containers` (and optional `--remote-images`)

## Driving it with CLI

Preconditions:

- Launch complete from repo root so workspace providers are on the entry-point path.
- For `--containers`: Docker CLI + Compose, daemon reachable. Skip that sub-feature without Docker.

- List plugins: `uv run --locked phlo plugin list --json` → exit 0; JSON object with `installed` array; entries include `type` values such as `cli` or provider types when those packages are installed.
- Validate plugins: `uv run --locked phlo plugin check --json` → exit 0; object has `valid` and `invalid`; `invalid` is `[]` on a healthy workspace; human mode without `--json` ends with `All plugins are valid!`.
- Containers (Docker only): `uv run --locked phlo plugin check --containers` → exit 0; stdout mentions generated Dockerfile checks. `--remote-images` without `--containers` is a UsageError.

## Gotchas

- `plugin check --json` is raw JSON (`valid`/`invalid`), not the init `data/warnings/errors` envelope.
- `--containers` generates a **temporary** user project internally; do not confuse it with `/tmp/phlo-verify-*` you created. It needs Docker images for hadolint/Trivy.
- A broken plugin can fail discovery for other commands; `phlo doctor` still loads on a fast path.
- Do not treat unit tests in `tests/cli/test_cli_plugin.py` as the user-visible proof; they are the harness, not the path.
