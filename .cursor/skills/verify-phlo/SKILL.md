---
name: verify-phlo
description: Verify Phlo (alpha lakehouse framework, 0.14.0) on the primary phlo CLI surface—plugin runtime, project layout, generated services, plugin check, and doctor. Reach for this skill when proving local CLI behavior in an isolated project; not for Observatory UI, docs, or marketing.
---

# Verify Phlo

Phlo is an AGPL-3.0-or-later **alpha** lakehouse framework. Public APIs and on-disk layout can move; this skill is pinned to **phlo 0.14.0** (workspace `pyproject.toml`). v1 support is **single-project, single-tenant**. Do not invent Kubernetes, HA, or multi-region checks.

**Primary surface:** the `phlo` CLI (`phlo = "phlo.cli.main:cli"`). Observatory is a provider UI, not this skill's verification surface. `phlo-api` is secondary (HTTP behind generated services). Drive CLI handles: command names, flags, stdout contracts, exit codes, generated files.

## Launch

Phlo is a CLI, not a long-running app. Launch means install deps once from this checkout, then each drive in its own isolated cwd.

1. Python **3.11 or 3.12** (CI support boundary). `uv` on PATH.
2. From the repo root, once per machine:

```bash
uv sync --locked
uv run --locked phlo --version
```

Ready when stdout is exactly:

```text
phlo, version 0.14.0
```

and exit code `0`. The binary must be the workspace package (`uv run --locked`), not a random global `phlo`.

3. Each drive uses a disposable project dir:

```bash
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
PROJECT="/tmp/phlo-verify-${RUN_ID}"
mkdir -p "$PROJECT"
```

Invoke `phlo` from that cwd (or pass an absolute path to `phlo init`). Do not drive a shared user project or this checkout's own tree.

**Teardown:** delete only `$PROJECT` after evidence is copied. If this run started services, stop them first with `phlo services stop` from that project cwd (then `phlo services reset --yes` only if this run created volumes). Never `killall` / pkill by process name. Cleanup never deletes evidence.

## Doctor

Run this read-only check first whenever anything looks off.

```bash
command -v uv
python3 -c 'import sys; v=sys.version_info; assert v[:2] in {(3,11),(3,12)}, v'
test -f pyproject.toml && grep -q '^name = "phlo"$' pyproject.toml
uv run --locked phlo --version
pwd
ls -d /tmp/phlo-verify-* 2>/dev/null || true
uv run --locked phlo doctor --json
```

Expect:

- `uv` present; Python 3.11 or 3.12.
- Cwd is the Phlo repo root (or an isolated project after `phlo init`).
- `--version` prints `phlo, version 0.14.0`.
- Leftover `/tmp/phlo-verify-*` dirs from earlier runs should be empty or explained; they are not a shared stack.
- `phlo doctor --json` is a JSON object with `summary` (`ok`/`warn`/`fail`/`skip` counts) and `checks[]` each having `id`, `group`, `status`, `message`. Exit `1` if any check `status` is `fail`.

On a CLI-only machine (no Docker daemon), `env.docker.cli` / compose probes **fail**. That blocks `phlo services start` / `status`, not `init`, `plugin check` (without `--containers`), or `--help`/`--version`. Do not treat a docker-missing doctor failure as a wrong binary.

## Drive

Prefer existing harnesses, then a PTY/CLI recipe.

**Harnesses in this repo (do not substitute product proof):**

- `uv run --locked pytest tests/cli/test_cli_init_templates.py` — template file contracts.
- `uv run --locked pytest tests/cli/test_cli_doctor.py` — doctor JSON/exit.
- `uv run --locked pytest tests/cli/test_cli_plugin.py` — `plugin list` / `plugin check --json`.
- `uv run --locked pytest tests/cli/test_quickstart_smoke.py` — init → services init → start with fakes (not a live Docker stack).

**CLI recipe (real user path):** from repo root after Launch:

```bash
.cursor/skills/verify-phlo/scripts/prove-project-init.sh
```

Or the same steps by hand (see `features/project-init.md`). Drive **one** mapped feature per proof run. Default proof target is **project-init** (no Docker). Map `services-generate` start/status only when Docker Compose v2 is healthy.

Stable handles:

| Handle | Contract |
| --- | --- |
| `phlo --version` | stdout `phlo, version 0.14.0`; exit 0 |
| `phlo --help` | lists `init`, `services`, `plugin`, `doctor`, `test`; exit 0 |
| `phlo init --list-templates --json` | envelope `{"data","warnings","errors"}`; `data.items[].name` includes `minimal`, `csv-batch` |
| `phlo init PATH --template csv-batch --json` | exit 0; `data.template` is `csv-batch`; writes `phlo.yaml`, `workflows/ingestion/csv/events.py` |
| `phlo plugin check --json` | exit 0 when `invalid` is empty; keys `valid` and `invalid` |
| `phlo doctor --json` | exit 0 only when no `fail` checks |
| `phlo services init` | writes `.phlo/docker-compose.yml`, `.phlo/.env`, `.phlo/.env.local`; stdout contains `Phlo infrastructure initialized.` |
| `phlo services start` / `status` | require container backend + generated compose; not CLI-only |

`--json` on init uses the shared envelope (`data` / `warnings` / `errors`). `plugin check --json` and `doctor --json` use their own shapes (not the envelope).

## Evidence

Capture under:

```text
.cursor/skills/verify-phlo/artifacts/runs/$RUN_ID/
```

That directory is gitignored. A small committed example lives at `.cursor/skills/verify-phlo/artifacts/project-init.example.md`. Proof standards:

- Real user path through `uv run --locked phlo …`, not pytest internals.
- Capture the **action** (full command, cwd, argv, stdout, stderr, exit code) **and** the **resulting state** (generated files, parsed JSON).
- Verify side effects: files exist and parse (`phlo.yaml` has `name:`; csv-batch writes `data/events.csv` and `@phlo.ingestion(`).
- Mocks only at production boundaries (container engine). This skill's default proof does not mock.
- If you use a dry-run (`phlo materialize … --dry-run`), capture stdout showing the command that would run and confirm no materialization side effects. Default proof does not use dry-run.

Minimum files in a run dir:

- `doctor.txt` — doctor command transcript
- `action.txt` — drive command + stdout/stderr + exit code
- `tree.txt` — generated project paths
- `summary.md` — what was proven

Copy `summary.md` (and short excerpts) to `artifacts/project-init.example.md` when refreshing the committed example. Evidence must remain after cleanup.

## Cleanup

1. Copy evidence out of `/tmp` first.
2. If this run started containers: from `$PROJECT`, `uv run --locked phlo services stop` (only that compose project). Kill only PIDs this run started.
3. `rm -rf "$PROJECT"` (the disposable `/tmp/phlo-verify-*` dir only).
4. Do not delete `.cursor/skills/verify-phlo/artifacts/`.
5. Do not `docker compose down` against any project you did not create.

## Helpers

`scripts/prove-project-init.sh` is executable. From repo root:

```bash
.cursor/skills/verify-phlo/scripts/prove-project-init.sh
```

Optional env: `RUN_ID`, `PHLO_VERIFY_TEMPLATE` (default `csv-batch`). Writes `artifacts/runs/$RUN_ID/` and refreshes `artifacts/project-init.example.md`. Removes `/tmp/phlo-verify-$RUN_ID` on success.

## Gotchas

- Providers generate Compose; do not hand-write `docker-compose.yml`.
- `phlo services start` / `status` / `plugin check --containers` need Docker with Compose v2. This VM may not run Docker; prove a CLI-only feature instead.
- Two CLI inits can run side by side. Two **started** stacks usually cannot: host ports collide. One live stack per machine unless you change ports in generated config.
- `phlo doctor` as a product command is not the same as this skill's Doctor section; still run product doctor and record its JSON.
- Do not expand Observatory UI or docs/marketing as verification surfaces.
- Pin 0.14.0 in reports; do not assume PyPI latest.
