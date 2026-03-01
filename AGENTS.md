# Agents Configuration for Phlo

Guidance for AI agents and developers in the Phlo monorepo.

**Work style:** Telegraph. Noun phrases ok. Minimal tokens.

## Principles

- Early stage: no backward-compat guarantees.
- Zero-debt bias: clean structure, explicit behavior, testability.
- No shims/placeholders/workarounds unless explicitly requested.
- Build for >1,000 users.
- User-visible changes: update docs.
- Keep files near <500 LOC; split when needed.
- Bug fixes: add regression test when practical.

## Monorepo Map

- `src/phlo/`: core CLI/runtime (config, discovery, hooks, services, logging).
- `packages/`: workspace packages (`phlo-dlt`, `phlo-dbt`, `phlo-dagster`, `phlo-quality`, `phlo-observatory`, ...).
- `tests/`: repo-level tests; package tests in `packages/*/tests`.
- `registry/`: plugin registry schema + metadata.
- `docs/`: docs site content.
- `scripts/`: developer automation.

## Commands

### Setup

```bash
uv pip install -e .
```

### Full Gate

```bash
make check
```

### Lint / Format / Types

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

### Tests

```bash
uv run pytest
```

### Services

```bash
phlo services start
phlo services stop
phlo services logs -f dagster-webserver
```

### dbt (services running)

```bash
docker exec dagster-webserver dbt run --select model_name
docker exec dagster-webserver dbt test --select tag:dataset_name
docker exec dagster-webserver dbt compile
```

## Architecture Snapshot

- Orchestration: Dagster assets + sensors.
- Ingestion: DLT + `@phlo_ingestion` (`phlo-dlt`).
- Quality: `@phlo_quality` + Pandera schemas (`phlo-quality`).
- Transforms: dbt models/medallion layers.
- Storage: Iceberg on S3-compatible MinIO + Nessie catalog.
- Query: Trino.
- Metadata: Postgres.
- UI/Observability: `phlo-observatory` + metrics/alerts packages.

## Coding Conventions

- Python 3.11+; line length 100.
- `ruff` for lint/format; `ty` for typecheck.
- Absolute imports only.
- Conventional Commits:
  `feat|fix|refactor|build|ci|chore|docs|style|perf|test`.
- Core config: `phlo.config.settings` (`.phlo/.env`, `.phlo/.env.local`).
- Service config: package-local settings modules.
- Template structure:
  - `workflows/` for ingestion/quality assets.
  - `workflows/transforms/dbt/` for dbt project.
  - `workflows/schemas/{domain}.py` for Pandera.
  - Asset names snake_case; ingestion assets `dlt_<table_name>`.
  - Database objects lowercase.

## Git and GitHub

- Safe defaults: `git status`, `git diff`, `git log`.
- Push only when user asks.
- Branch changes need user consent.
- No destructive commands unless explicit user request (`reset --hard`, `clean`, `restore`, `rm`, ...).
- If unexpected file deletions/renames appear: stop and ask.
- Avoid manual `git stash`; auto-stash during Git workflows is fine.
- No amend unless user asks.
- Large review command: `git --no-pager diff --color=never`.
- Never mention yourself in commit messages/PRs.

### `gh` CLI

- Use `gh` for issues/PRs/CI/releases; avoid web-search fallback for GitHub data.
- Issue example: `gh issue view <url> --comments -R owner/repo`.
- PR example: `gh pr view <url> --comments --files -R owner/repo`.

## Docs Standards

- Put docs in the right lane:
  `docs/getting-started/`, `docs/guides/`, `docs/reference/`, `docs/setup/`,
  `docs/operations/`, `docs/packages/`, `docs/architecture/decisions/`, `docs/errors/`.
- If adding/moving pages, update `docs/index.md` links in same change.
- CLI behavior/flags/output changes:
  update `docs/reference/cli-reference.md` plus related guides.
- Config/env/default changes:
  update `docs/reference/configuration-reference.md` and package docs under `docs/packages/`.
- Service ports/profiles/startup behavior:
  keep docs aligned with package `service.yaml` files and actual CLI behavior.
- Plugin entry-point docs source of truth:
  `src/phlo/plugins/discovery/_plugin_constants.py` (`ENTRY_POINT_GROUPS`).
- Ingestion/quality docs prefer `import phlo` then `phlo.ingestion` /
  `phlo.quality` usage.
- dbt profiles path remains `workflows/transforms/dbt/profiles/profiles.yml`.
- Observatory extension docs source of truth:
  `packages/phlo-observatory/src/phlo_observatory/manifest.py`,
  `packages/phlo-observatory/src/phlo_observatory/observatory_ext.py`,
  example at `packages/phlo-observatory-example/src/phlo_observatory_example/observatory_plugin.py`.
- New/changed error codes:
  add or update `docs/errors/PHLO-*.md` and `docs/reference/common-errors.md`.

## Runtime and Validation

- Long jobs: Codex background mode.
- tmux only for persistent interactive sessions (debugger/server).
- Before handoff: run full gate (lint, typecheck, tests, docs checks as relevant).
- CI red loop: inspect (`gh run list/view`), rerun, fix, push, repeat until green.
- Keep execution observable (logs/panes/tails).

## PR Feedback Workflow

- Active PR summary:
  `gh pr view --json number,title,url --jq '"PR #\\(.number): \\(.title)\\n\\(.url)"'`
- Comment retrieval:
  `gh pr view ...` plus `gh api .../comments --paginate`
- Reply policy: cite fix + file/line; resolve threads only after fix lands.

## Decision Standard

- Fix root cause; avoid band-aids.
- If unsure: read code deeper first.
- If still blocked: ask user with short concrete options.
- Call out conflicting constraints; choose safer path.
- Prefer end-to-end verification; if blocked, state exact gap.
- Leave short breadcrumb notes in thread.

## Tool Notes

### tmux

- Use only for persistent/interactive sessions.
- Quick refs:
  `tmux new -d -s codex-shell`
  `tmux attach -t codex-shell`
  `tmux list-sessions`
  `tmux kill-session -t codex-shell`
