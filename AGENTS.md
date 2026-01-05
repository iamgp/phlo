# Agents Configuration for Phlo

Guidelines for AI agents and developers working on the Phlo monorepo.

**Work style:** Telegraph. Noun-phrases ok; drop grammar; minimize tokens globally.

## Development Principles

- Early stage: no backward compatibility guarantees.
- Keep code clean and organized; aim for zero technical debt.
- Implement features properly to scale beyond 1,000 users.
- Avoid compatibility shims, workarounds, and placeholders.
- Prefer explicit, testable behavior; update docs for user-visible changes.
- Keep files <~500 LOC; split/refactor as needed.
- Bugs: add regression test when it fits.

## Repository Layout (Monorepo)

- `src/phlo/` - Core CLI/runtime (config, discovery, hooks, services, logging).
- `packages/` - Workspace packages (phlo-dlt, phlo-dbt, phlo-dagster, phlo-quality, phlo-observatory, etc.).
- `tests/` - Repo-level tests; package tests live in `packages/*/tests`.
- `registry/` - Plugin registry schema + published metadata.
- `docs/` - Documentation site content.
- `scripts/` - Developer automation helpers.

## Tooling & Commands

### Setup

```bash
uv pip install -e .
```

### All Checks

```bash
make check
```

### Python Quality

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

### Tests

```bash
uv run pytest
```

### Dependencies

- New deps: quick health check (recent releases/commits, adoption).

### Services

```bash
phlo services start
phlo services stop
phlo services logs -f dagster-webserver
```

### dbt (when services are running)

```bash
docker exec dagster-webserver dbt run --select model_name
docker exec dagster-webserver dbt test --select tag:dataset_name
docker exec dagster-webserver dbt compile
```

## Architecture Snapshot

- Orchestration: Dagster assets + sensors.
- Ingestion: DLT + `@phlo_ingestion` decorator (phlo-dlt).
- Quality: `@phlo_quality` + Pandera schemas (phlo-quality).
- Transformations: dbt for SQL models and medallion layers.
- Storage: Iceberg tables on S3-compatible storage (MinIO) with Nessie catalog.
- Query: Trino.
- Metadata: Postgres (operational metadata and marts).
- UI/Observability: phlo-observatory plus metrics/alerting packages.

## Conventions

- Python 3.11+, line length 100.
- Type checking: ty.
- Lint/format: ruff.
- Absolute imports only.
- Commits follow Conventional Commits (`feat|fix|refactor|build|ci|chore|docs|style|perf|test`).
- Configuration via `phlo.config.settings` (reads `.phlo/.env` and `.phlo/.env.local`).
- Project templates use:
    - `workflows/` for ingestion/quality assets and `workflows/transforms/dbt/` for dbt projects.
    - Pandera schemas in `workflows/schemas/{domain}.py`.
    - Asset names in snake*case; ingestion assets use `dlt*<table_name>`.
    - Database objects in lowercase.

## Git

- Safe by default: `git status/diff/log`. Push only when user asks.
- `git checkout` ok for PR review / explicit request.
- Branch changes require user consent.
- Destructive ops forbidden unless explicit (`reset --hard`, `clean`, `restore`, `rm`, …).
- Don't delete/rename unexpected stuff; stop + ask.
- Avoid manual `git stash`; if Git auto-stashes during pull/rebase, that's fine.
- If user types a command ("pull and push"), that's consent for that command.
- No amend unless asked.
- Big review: `git --no-pager diff --color=never`.
- Never mention yourself in commit messages or pull requests.

### gh

- GitHub CLI for PRs/CI/releases. Given issue/PR URL (or `/pull/5`): use `gh`, not web search.
- Examples: `gh issue view <url> --comments -R owner/repo`, `gh pr view <url> --comments --files -R owner/repo`.

## Flow & Runtime

- Use Codex background for long jobs; tmux only for interactive/persistent (debugger/server).

## Build / Test

- Before handoff: run full gate (lint/typecheck/tests/docs).
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Keep it observable (logs, panes, tails).

## PR Feedback

- Active PR: `gh pr view --json number,title,url --jq '"PR #\\(.number): \\(.title)\\n\\(.url)"'`.
- PR comments: `gh pr view …` + `gh api …/comments --paginate`.
- Replies: cite fix + file/line; resolve threads only after fix lands.

## Critical Thinking

- Fix root cause (not band-aid).
- Unsure: read more code; if still stuck, ask w/ short options.
- Conflicts: call out; pick safer path.
- Prefer end-to-end verify; if blocked, say what's missing.
- Leave breadcrumb notes in thread.

## Tools

### tmux

- Use only when you need persistence/interaction (debugger/server).
- Quick refs: `tmux new -d -s codex-shell`, `tmux attach -t codex-shell`, `tmux list-sessions`, `tmux kill-session -t codex-shell`.

### Slash Commands

- Global: `~/.codex/prompts/`. Repo-local: `docs/slash-commands/`.
- Common: `/handoff`, `/pickup`.

### mcporter / MCP

- MCP launcher: `npx mcporter <server>` (see `npx mcporter --help`). Common: `iterm`, `firecrawl`, `XcodeBuildMCP`.

### gh

- GitHub CLI for PRs/CI/releases. Given issue/PR URL (or `/pull/5`): use `gh`, not web search.
- Examples: `gh issue view <url> --comments -R owner/repo`, `gh pr view <url> --comments --files -R owner/repo`.
