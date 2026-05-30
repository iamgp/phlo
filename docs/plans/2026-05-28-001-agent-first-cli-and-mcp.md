---
title: "feat: Agent-first Phlo CLI and MCP"
type: plan
status: completed
date: 2026-05-28
origin: thread/T-019e7082-9716-74d5-950b-07d6ef3e8575
supersedes: []
related:
  - docs/plans/2026-04-25-002-phlo-mcp-operational-tools.md
  - docs/plans/2026-04-25-003-phlo-mcp-trace-filtering.md
  - docs/plans/2026-04-25-004-phlo-mcp-resources.md
  - docs/plans/2026-04-25-005-phlo-mcp-e2e-smoke.md
  - docs/plans/2026-04-26-001-phlo-doctor.md
  - docs/plans/2026-04-26-002-authoring-path-polish.md
---

# Agent-first Phlo CLI and MCP

## Overview

Make `phlo` (CLI) and `phlo-mcp` (MCP server) the best-in-class surface for
coding agents to author workflows, inspect runs, diagnose failures, and operate
the lakehouse — safely.

The MCP server today is read-strong but operate-weak: agents can inspect almost
everything but cannot complete an end-to-end author → validate → materialize →
inspect → retry loop without a human. The CLI is broad but only one command
(`phlo doctor`) speaks JSON; agents shelling out get prose.

This plan closes the loop in four phases. Phases are sequenced so each phase is
shippable on its own and each later phase composes on earlier ones.

## Goals

1. An agent connected to Phlo via MCP can complete the full lifecycle of a
   lakehouse asset — scaffold, validate, materialize, inspect a run, diagnose
   a failure, retry — without shelling out or asking a human to run commands.
2. Every CLI command an agent might invoke supports `--json` with a stable,
   documented envelope.
3. Every MCP tool advertises a typed input and output schema so MCP clients can
   validate calls before sending them.
4. Mutations are safe by default: scoped tokens, dry-run defaults, idempotency
   keys, audit logs.
5. New `phlo init` projects ship with an `AGENTS.md` that teaches agents which
   tools to prefer for which task.

## Non-goals

- Building a "do-everything" agent. Phlo provides the surface; clients (Claude
  Code, Amp, Cursor, custom orchestrators) bring the agent.
- Replacing Dagster's GraphQL API. `phlo-api` remains the only thing MCP talks
  to; we do not let MCP reach Dagster, Loki, or ClickStack directly.
- Multi-tenant SaaS. Single-project, single-stack assumptions hold.

## Current state (May 2026)

Strengths (keep):

- 15 read MCP tools + 10 deterministic resources (see
  [phlo-mcp README](../../packages/phlo-mcp/README.md))
- OTEL tracing on every tool invocation
- Trace-tree text renderers (`render_*_trace_tree`)
- Write-tool gate (`PHLO_MCP_ENABLE_WRITE_TOOLS` + bearer token, default
  `dry_run=true`, structured `audit_context`)
- Live-stack smoke harness ([smoke_stack.py](../../packages/phlo-mcp/tests/smoke_stack.py))
- Stdio + streamable-HTTP transports

Gaps (close):

| # | Gap | Closed in phase |
|---|---|---|
| G1 | `materialize_asset` / `retry_failed_run` are dry-run stubs | 1 |
| G2 | No MCP tool for workflow authoring | 2 |
| G3 | No MCP `validate_workflow` / `validate_schema` / `lint_project` | 2 |
| G4 | No MCP `run_doctor` mirroring `phlo doctor --json` | 2 |
| G5 | No `backfill_asset` / `cancel_run` / `partition_status` | 1 |
| G6 | No `list_workflows` / `search_assets` / `search_contracts` | 2 |
| G7 | Tools return `dict[str, Any]` with no JSON Schema | 3 |
| G8 | No pagination cursors | 3 |
| G9 | No log search / regex / text filter | 3 |
| G10 | No `@mcp.prompt` definitions | 1 |
| G11 | `--json` not universal across CLI | 4 |
| G12 | No CLI / MCP introspection resources | 3 |
| G13 | HTTP errors surface raw `httpx` exceptions | 3 |
| G14 | No streaming / follow for run logs over MCP | 3 |
| G15 | `phlo-mcp` not surfaced under `phlo mcp …` | 4 |
| G16 | No `AGENTS.md` template in starters | 4 |
| G17 | Plugin lifecycle not on MCP | 4 |
| G18 | No schema-diff MCP tool | 3 |
| G19 | No quality-results MCP tool | 3 |
| G20 | No lineage-graph MCP tool | 3 |

## Phases

### Phase 1 — Close the operate loop

> Goal: an agent that can already inspect a run can also cause new runs, retry
> failed ones, cancel runaway ones, and backfill partitions — safely.

This is the biggest blocker today; the README of `phlo-mcp` says outright:
*"live Dagster launch and retry are intentionally not implemented yet."*

#### 1.1 Implement live Dagster launch/retry in `phlo-api`

- `packages/phlo-api/src/phlo_api/api/operations.py` (new):
  - `POST /api/observatory/v2/assets/{asset_key_path}/materialize`
    - Body: `{ dry_run: bool, partition_key: str | None, partition_range: {start,end} | None, idempotency_key: str | None, tags: dict[str,str] | None }`
    - When `dry_run=true`: validate that asset exists, partition is valid, user
      is authorised; return the launch plan without launching.
    - When `dry_run=false`: call Dagster GraphQL `launchPipelineExecution`
      (or asset-graph equivalent) via existing `phlo-dagster` capability.
    - Response: `{ run_id, status, launch_plan, idempotency_key }`.
  - `POST /api/observatory/v2/runs/{run_id}/retry`
    - Body: `{ dry_run: bool, strategy: "from_failure" | "full", idempotency_key }`
    - Calls Dagster `launchRunReexecution` with the right policy.
  - `POST /api/observatory/v2/runs/{run_id}/cancel`
    - Body: `{ reason: str | None }`
    - Calls Dagster `terminateRun`.
  - `POST /api/observatory/v2/assets/{asset_key_path}/backfill`
    - Body: `{ dry_run, partitions: [str] | partition_range, idempotency_key, tags }`
    - Calls Dagster `launchPartitionBackfill`.
  - `GET /api/observatory/v2/assets/{asset_key_path}/partitions`
    - Lists partition keys + materialization status for each.

- Capability contract: extend
  [`phlo-dagster`](../../packages/phlo-dagster/) capability with
  `launch_materialize`, `launch_retry`, `terminate`, `launch_backfill`,
  `list_partitions`. Keep all Dagster GraphQL access inside the capability.

- Idempotency: persist `(idempotency_key, operation, target)` in
  `.phlo/state/operations.sqlite` for a configurable retention window; replays
  return the original `run_id`.

- Authorisation: every mutation route requires the existing
  bearer-token + capability scope check (see plan
  [2026-04-25-001-phlo-mcp-api-auth.md](2026-04-25-001-phlo-mcp-api-auth.md)).
  Add a new scope `lakehouse:operate` distinct from `lakehouse:read`.

#### 1.2 Wire MCP write tools end-to-end

- `packages/phlo-mcp/src/phlo_mcp/api_client.py`:
  - Implement `materialize_asset`, `retry_run`, `cancel_run`, `backfill_asset`,
    `list_partitions` as real calls (not stubs).
- `packages/phlo-mcp/src/phlo_mcp/server.py`:
  - Replace stub `materialize_asset` and `retry_failed_run` bodies with real
    calls; keep `dry_run=true` default; keep `audit_context`.
  - Add new guarded tools: `cancel_run`, `backfill_asset`, `list_partitions`.
- `packages/phlo-mcp/tests/test_phlo_mcp.py`: dry-run and live paths,
  idempotency-key replay, scope-denied path.
- `packages/phlo-mcp/tests/smoke_stack.py`: add `--exercise-live-write-tools`
  flag that actually launches a tiny no-op asset on a throwaway project.

#### 1.3 Add MCP prompts (`@mcp.prompt`)

Canned, parameterised prompt templates so MCP clients show "Phlo: …" actions:

- `phlo.debug_run(run_id)` — instructs the agent to fetch logs + spans, render
  the tree, identify the failing span, and propose a fix.
- `phlo.triage_failure(asset_key)` — fetches latest materialisation, run logs,
  quality results, and proposes remediation.
- `phlo.audit_asset(asset_key)` — runs the full health pass on one asset.
- `phlo.plan_backfill(asset_key, range)` — produces a dry-run plan + caveats.
- `phlo.scaffold_workflow(domain, table)` — defers to phase-2 tool but the
  prompt is added here.

#### 1.4 Deliverables

- New routes shipping in `phlo-api` ≥ next minor.
- 6 new MCP tools wired end-to-end.
- 4–5 MCP prompts shipping.
- Capability scope `lakehouse:operate` in
  [auth-and-access docs](../reference/auth-and-access.md).
- ADR: `docs/plans/2026-05-28-002-lakehouse-operate-scope.md` (split out).

#### 1.5 Verification

```bash
uv run pytest packages/phlo-api/tests -q
uv run pytest packages/phlo-mcp/tests -q
uv run python packages/phlo-mcp/tests/smoke_stack.py \
  --start-stack --enable-write-tools \
  --api-token "$PHLO_MCP_SMOKE_API_TOKEN" \
  --exercise-live-write-tools
```

### Phase 2 — Author + validate loop

> Goal: an agent can scaffold a new workflow, validate it, and materialise it,
> all through MCP. Today scaffolding is gated behind `click.prompt`.

#### 2.1 De-interactive the scaffolders

- [`src/phlo/cli/commands/workflow.py`](../../src/phlo/cli/commands/workflow.py):
  split `create_workflow_cmd` into:
  - `_create_workflow(domain, table, unique_key, cron, api_base_url, fields) -> CreateWorkflowResult` (pure, no Click)
  - `create_workflow_cmd` (thin Click wrapper)
- Same treatment for any `click.prompt` in
  [`src/phlo/cli/commands/plugin/scaffold.py`](../../src/phlo/cli/commands/plugin/scaffold.py)
  and other interactive scaffolders.

#### 2.2 Add authoring/validate routes to `phlo-api`

- `packages/phlo-api/src/phlo_api/api/authoring.py` (new):
  - `POST /api/authoring/workflows` — body matches `_create_workflow`; returns
    created files + next-steps JSON.
  - `POST /api/authoring/workflows/validate` — body `{ workflow_path }`.
  - `POST /api/authoring/schemas/validate` — body `{ schema_path }`.
  - `GET  /api/authoring/templates` — list starters + required packages.
  - `GET  /api/authoring/workflows` — list workflows discovered in project.
  - `POST /api/authoring/project/lint` — runs project-wide lint checks
    (`phlo doctor` + `phlo workflow check` for all workflows).

These mutate the project's filesystem, so they require `project:write` scope
(new) distinct from `lakehouse:operate`.

#### 2.3 Add MCP tools

- `create_workflow(domain, table, unique_key, cron, api_base_url?, fields?)`
- `validate_workflow(workflow_path)`
- `validate_schema(schema_path)`
- `list_workflows(search?, group?)`
- `list_templates()`
- `lint_project()`
- `run_doctor()` — mirrors `phlo doctor --json`

Plus search/discovery:

- `search_assets(query, limit, cursor)` — server-side prefix + substring search
- `search_contracts(query, limit, cursor)`
- `search_runs(filters, cursor)` — wraps the existing trace search but adds
  status + time + asset filters in a single call.

#### 2.4 Make `phlo doctor` an MCP tool

The CLI already supports `--json`. Either:

- (a) `phlo-api` exposes `GET /api/doctor` that runs the same checks, or
- (b) MCP tool shells out to `phlo doctor --json`.

Prefer (a) for consistency with the rest of the API surface; reuse the existing
[`doctor` command](../../src/phlo/cli/commands/doctor.py) by extracting the
diagnostic engine from the Click command into a library function.

#### 2.5 Deliverables

- 10 new MCP tools.
- 6 new `phlo-api` routes.
- `phlo doctor` diagnostic engine extracted into a pure library function.

#### 2.6 Verification

```bash
uv run pytest packages/phlo-api/tests/test_authoring_api.py -q
uv run pytest packages/phlo-mcp/tests -q
# Round-trip:
phlo init demo --template csv-batch
# Via MCP only:
#   create_workflow → validate_workflow → materialize_asset(dry_run=true)
#   → list_workflows → inspect_materialization
```

### Phase 3 — Agent ergonomics

> Goal: every interaction returns predictable shapes, scales to large
> lakehouses, and fails with actionable errors.

#### 3.1 Typed responses + JSON Schema

- Add `packages/phlo-mcp/src/phlo_mcp/models.py` with Pydantic models for every
  tool response. Use `model_json_schema()` to populate FastMCP
  `output_schema`.
- Same exercise on the `phlo-api` side using FastAPI's existing
  `response_model=` so the schemas match.
- `mcp.tool()` calls become:

  ```python
  @mcp.tool(output_schema=GetRunLogsResponse.model_json_schema())
  def get_run_logs(...): ...
  ```

#### 3.2 Cursor-based pagination

- All list/search tools accept `cursor: str | None` and return
  `{ items, next_cursor }`. Use opaque base64-encoded cursors so the server can
  change the implementation without breaking clients.
- Tools affected: `get_recent_alerts`, `get_materialization_history`,
  `get_run_logs`, `get_trace_spans`, `list_workflows`, `search_*`,
  `runtime/assets` (when materialized as a tool).

#### 3.3 Structured error envelope

- Wrap `_get_json` / `_post_json` in `api_client.py`:

  ```python
  class PhloMcpError(Exception):
      code: str        # e.g. "asset.not_found"
      message: str     # human
      hint: str | None # one-liner remediation
      docs_url: str | None
      retryable: bool
  ```

- Map common `httpx.HTTPStatusError` cases to error codes; everything else
  becomes `phlo.api.unknown` with the original message preserved.
- MCP returns errors as a structured object in the tool result (not a raw
  exception), so agents can branch on `code`.

#### 3.4 Log search + follow

- `phlo-api`:
  - Extend `GET /api/loki/runs/{run_id}` with `query`, `regex`, `since`,
    `until`, `cursor`.
  - Add `GET /api/loki/runs/{run_id}/stream` (SSE) for tail-follow.
- `phlo-mcp`:
  - `search_run_logs(run_id, query, regex?, since?, until?, cursor?)`.
  - `follow_run_logs(run_id, timeout_seconds=30)` — bounded streamable-HTTP
    tool that yields chunks until timeout or run completion.

#### 3.5 Quality, lineage, schema-diff tools

- `get_quality_results(asset_key, run_id?)` — surfaces Pandera failure rows,
  rule name, severity, sample rows.
- `get_lineage(asset_key, direction=upstream|downstream|both, depth=1)` —
  walks the asset graph.
- `diff_schema(asset_key, from_run, to_run)` — wraps `schema-migrate diff`.

#### 3.6 Self-introspection resources

- `phlo://docs/cli` — Markdown index of CLI commands, generated from Click
  introspection so it stays accurate.
- `phlo://docs/mcp/tools` — JSON list of MCP tools with input/output schemas.
- `phlo://docs/mcp/prompts` — JSON list of MCP prompts.

Generate these at server start so agents can introspect without reading
package docs.

#### 3.7 Deliverables

- Pydantic models for ~25 tool responses.
- Pagination across all list tools.
- Error envelope with ≥20 named codes.
- 3 new observability tools + 2 new introspection resources.

#### 3.8 Verification

```bash
uv run pytest packages/phlo-mcp/tests/test_models.py -q
uv run pytest packages/phlo-mcp/tests/test_pagination.py -q
uv run pytest packages/phlo-mcp/tests/test_errors.py -q
```

Add a contract test that asserts every `@mcp.tool` has an `output_schema`.

### Phase 4 — Discoverability + safety

> Goal: humans installing Phlo discover the MCP without reading the README;
> agents in a new project find an `AGENTS.md` telling them what to use;
> mutations leave an audit trail you can grep.

#### 4.1 `phlo mcp` subcommand

- New `src/phlo/cli/commands/mcp/` group:
  - `phlo mcp serve [--transport stdio|streamable-http] [--api-base-url …]`
    — wraps the existing `phlo-mcp` entrypoint so `phlo-mcp` becomes an
    implementation detail.
  - `phlo mcp install <client>` where `<client>` ∈ {`claude-code`, `amp`,
    `cursor`, `vscode`} writes the appropriate config block to the right file.
  - `phlo mcp tools` and `phlo mcp prompts` — list registered tools/prompts
    locally without starting the server.
  - `phlo mcp config` — print resolved config (redacted).
- Keep `phlo-mcp` console script alive as an alias for one minor.

#### 4.2 `--json` everywhere

- Add a shared `phlo.cli.output.json_envelope({ data, warnings, errors })`
  helper.
- Sweep `src/phlo/cli/commands/**/*.py` adding `--json` to every command,
  using the helper. Start with read-heavy commands:
  `services list/status`, `catalog tables`, `lineage show`, `status`,
  `workflow check`, `contracts list`, `plugin list/info`, `schema list`.
- Then mutators: emit a per-action JSON line on success/failure so agents can
  parse without screen-scraping.
- Add `--quiet` / `--no-color` for agent-friendly output.

#### 4.3 Capability scopes on tokens

- Token claims grow scopes: `lakehouse:read`, `lakehouse:operate`,
  `project:write`, `admin`.
- `phlo-api` enforces per-route; `phlo-mcp` advertises required scope per tool.
- Document in [auth-and-access](../reference/auth-and-access.md).

#### 4.4 Audit log sink

- Every write call (Phase 1 + Phase 2) appends a JSONL record to
  `.phlo/audit/operations.jsonl` (or whatever sink is configured) with the
  full `audit_context` plus resolved scopes and token subject.
- Add `phlo audit tail` / `phlo audit query` CLI.

#### 4.5 Rate limits

- Per-token token-bucket on mutation routes in `phlo-api`. Defaults:
  - `materialize/backfill`: 10/min
  - `retry`: 30/min
  - `cancel`: 60/min
- Override via config.

#### 4.6 `AGENTS.md` in starters

- Add `AGENTS.md` template to each starter
  ([`src/phlo/cli/templates/`](../../src/phlo/cli/templates/)):
  - csv-batch
  - rest-api
  - dbt-medallion
  - sling
  - observatory-demo
- Content: which MCP tools to prefer for which task, which resources to attach,
  scope hints, sample prompts.
- Also add an `AGENTS.md` section to the project [`AGENTS.md`](../../AGENTS.md)
  for repo contributors.

#### 4.7 Deliverables

- `phlo mcp` command group with `serve|install|tools|prompts|config`.
- `--json` on every CLI subcommand.
- Token scopes documented + enforced.
- Audit log on disk + CLI to query it.
- `AGENTS.md` shipped in 5 starters.

#### 4.8 Verification

```bash
uv run pytest tests/cli -q
uv run pytest packages/phlo-api/tests/test_rate_limits.py -q
phlo mcp install claude-code --dry-run
phlo mcp tools --json | jq '.[] | .name'
phlo audit tail --since 1h --json | jq .
```

## Cross-cutting decisions

### Capability layering

```diagram
╭───────────────────────╮
│ MCP client (Amp/etc.) │
╰──────────┬────────────╯
           │ stdio | streamable-http
╭──────────▼────────────╮     ╭─────────────────╮
│       phlo-mcp        │◀───▶│ phlo://… resrcs │
╰──────────┬────────────╯     ╰─────────────────╯
           │ HTTP + bearer + scopes
╭──────────▼────────────╮
│       phlo-api        │
╰──────────┬────────────╯
           │ capability calls
   ╭───────┼────────┬──────────┬───────────╮
   ▼       ▼        ▼          ▼           ▼
╭──────╮ ╭──────╮ ╭─────────╮ ╭────────╮ ╭───────╮
│dagstr│ │loki  │ │clickstck│ │catalog │ │authz  │
╰──────╯ ╰──────╯ ╰─────────╯ ╰────────╯ ╰───────╯
```

Rule: MCP only talks to `phlo-api`. `phlo-api` only talks to capabilities.
No backend (Dagster GraphQL, Loki, ClickStack) is ever called directly from
MCP.

### Scope model

| Scope | Read | Write | Examples |
|---|---|---|---|
| `lakehouse:read` | yes | no | every existing read tool |
| `lakehouse:operate` | yes | yes (data plane) | materialize, retry, cancel, backfill |
| `project:write` | yes | yes (project files) | create_workflow, lint, scaffold |
| `admin` | yes | yes (all) | plugin install, authz sync |

### Backwards compatibility

- All existing MCP tool names and resource URIs remain unchanged.
- Tool responses gain new fields only — existing fields are not renamed or
  removed in this plan.
- `phlo-mcp` console script stays for one minor after `phlo mcp serve` lands.

## Sequencing and parallelism

```diagram
Phase 1  ─────────────▶ Phase 2  ─────────────▶ Phase 3 ────────────▶ Phase 4
   │                       │                       │                     │
   ├── 1.1 phlo-api ops    ├── 2.1 de-interactive  ├── 3.1 typed models  ├── 4.1 phlo mcp cmd
   ├── 1.2 mcp wire-up     ├── 2.2 authoring API   ├── 3.2 pagination    ├── 4.2 --json sweep
   ├── 1.3 prompts         ├── 2.3 mcp tools       ├── 3.3 error model   ├── 4.3 scopes
   └── 1.4 scope+audit     ├── 2.4 doctor library  ├── 3.4 log search    ├── 4.4 audit log
                           └── 2.5 search tools    ├── 3.5 q/l/diff     ├── 4.5 rate limits
                                                   └── 3.6 introspect    └── 4.6 AGENTS.md
```

Within a phase, items can be parallelised: each numbered item is a separate
PR, owned by one author, and unblocked by the others in the same phase. Phase
boundaries are hard gates because later phases assume the API surface from
earlier phases.

## Estimated effort

(Rough, intended for sequencing not commitment.)

| Phase | Engineer-weeks | Notes |
|---|---|---|
| 1 | 3 | Live Dagster launch is the biggest single item. |
| 2 | 2 | Mostly de-interactive plumbing + thin API. |
| 3 | 2 | Models + pagination is mechanical; SSE for follow is the only spike. |
| 4 | 2 | CLI sweep + docs + audit. |
| **Total** | **≈ 9** | Single full-time engineer ≈ 10–12 weeks elapsed. |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Dagster GraphQL surface drifts across versions | Pin per-capability adapter; integration test on a known Dagster image in CI. |
| MCP clients differ in how they render structured tool errors | Make the error envelope serialisable to plain text via `__str__`; include rendered message for naive clients. |
| Adding `--json` everywhere causes prose-output regressions | Default stays human; `--json` is opt-in; snapshot tests on human output. |
| Scope creep on prompts | Cap initial prompt count at 5; add new ones only when a real client needs one. |
| Audit log grows unboundedly | Ship rotation (`size` + `time`) in Phase 4.4; document retention. |
| Idempotency keys leak across projects | Key is namespaced by project + workspace ID; tests cover the boundary. |

## Verification matrix

| Capability | Test layer |
|---|---|
| phlo-api routes | `packages/phlo-api/tests` (httpx test client) |
| Capability adapters | per-package tests (`phlo-dagster`, `phlo-loki`, …) |
| MCP tool registration + dispatch | `packages/phlo-mcp/tests/test_phlo_mcp.py` |
| MCP schemas | new `tests/test_models.py` |
| Pagination | new `tests/test_pagination.py` |
| Errors | new `tests/test_errors.py` |
| End-to-end | `packages/phlo-mcp/tests/smoke_stack.py` with new flags |
| CLI JSON envelopes | snapshot tests in `src/phlo/cli/tests` |
| Audit log | round-trip test: mutate via MCP, read via `phlo audit query` |

## Outcome

Completed in `e60dc02d3d` plus the follow-up completion pass in this thread.

- MCP now supports the full scaffold → validate → materialize/backfill → inspect → retry/cancel loop through `phlo-api` only.
- Mutating routes enforce scoped tokens, rate limits, idempotency replay, and JSONL audit records with rotation.
- Agent-facing authoring, doctor, search, log-follow, quality, lineage, schema-diff, and plugin-install tools are available through MCP.
- MCP self-introspection resources expose registered tools, prompts, required scopes, and CLI command documentation.
- `phlo mcp` and `phlo audit` command groups provide local discoverability and audit inspection; key agent-facing CLI commands emit JSON envelopes.
- New projects generated by `phlo init` include an `AGENTS.md` with MCP-first guidance.

## Appendix A — Tool inventory after Phase 4

Read tools (existing + new):

- `get_platform_health`, `get_service_status`, `get_recent_alerts`,
  `get_dashboard_links`, `get_logs_query_link`, `get_metrics_query_link`,
  `get_materialization_history`, `get_run_logs`, `get_run_trace_spans`,
  `get_trace_spans`, `render_trace_spans_tree`, `inspect_materialization`,
  `get_asset_materialization_trace`, `render_materialization_trace_tree`,
  `render_run_trace_tree`
- **new:** `list_workflows`, `list_templates`, `search_assets`,
  `search_contracts`, `search_runs`, `search_run_logs`, `follow_run_logs`,
  `get_quality_results`, `get_lineage`, `diff_schema`, `run_doctor`,
  `list_partitions`

Write tools (guarded):

- `materialize_asset` (live), `retry_failed_run` (live),
  `get_dagster_run_status`
- **new:** `cancel_run`, `backfill_asset`, `create_workflow`,
  `validate_workflow`, `validate_schema`, `lint_project`

Prompts:

- `phlo.debug_run`, `phlo.triage_failure`, `phlo.audit_asset`,
  `phlo.plan_backfill`, `phlo.scaffold_workflow`

Resources:

- All existing `phlo://runtime/*` and `phlo://docs/packages/{name}`
- **new:** `phlo://docs/cli`, `phlo://docs/mcp/tools`, `phlo://docs/mcp/prompts`

## Appendix B — Task breakdown

Each task is a single, independently-grabbable unit of work — sized to one PR.
Tasks within a phase can be parallelised unless a `depends:` line says
otherwise. Phase boundaries are hard gates: do not start a Phase N+1 task
until the Phase N tasks it depends on are merged.

Status legend: `[ ]` proposed · `[~]` in progress · `[x]` complete · `[-]` dropped

### Phase 1 — Close the operate loop

- [x] **P1-T01** — Extend `phlo-dagster` capability with `launch_materialize`,
  `launch_retry`, `terminate`, `launch_backfill`, `list_partitions`.
  - Files: `packages/phlo-dagster/src/phlo_dagster/operations.py` (new)
  - Tests: `packages/phlo-dagster/tests/test_operations.py`
  - depends: none

- [x] **P1-T02** — Add `POST /api/observatory/v2/assets/{asset_key_path}/materialize`
  to `phlo-api` with dry-run + live paths.
  - Files: `packages/phlo-api/src/phlo_api/api/operation_controls.py`,
    `packages/phlo-api/src/phlo_api/observatory_api/orchestrator_operations.py`,
    registered through `packages/phlo-api/src/phlo_api/api/__init__.py`
  - depends: P1-T01

- [x] **P1-T03** — Add `POST /api/observatory/v2/runs/{run_id}/retry`.
  - depends: P1-T01

- [x] **P1-T04** — Add `POST /api/observatory/v2/runs/{run_id}/cancel`.
  - depends: P1-T01

- [x] **P1-T05** — Add `POST /api/observatory/v2/assets/{asset_key_path}/backfill`.
  - depends: P1-T01

- [x] **P1-T06** — Add `GET /api/observatory/v2/assets/{asset_key_path}/partitions`.
  - depends: P1-T01

- [x] **P1-T07** — Idempotency-key store at
  `.phlo/state/operations.sqlite` with replay semantics.
  - Files: `packages/phlo-api/src/phlo_api/operations/idempotency.py` (new)
  - Tests: replay returns original `run_id`; expiry; cross-project isolation
  - depends: none (lands in parallel with P1-T02..T05)

- [x] **P1-T08** — Add `lakehouse:operate` scope; enforce on every operation
  route from P1-T02..T05.
  - Files: `packages/phlo-api/src/phlo_api/api/authorization.py`,
    [docs/reference/auth-and-access.md](../reference/auth-and-access.md)
  - depends: P1-T02..T05 stubs landed

- [x] **P1-T09** — Wire real `materialize_asset` in
  [`api_client.py`](../../packages/phlo-mcp/src/phlo_mcp/api_client.py) and
  [`server.py`](../../packages/phlo-mcp/src/phlo_mcp/server.py); remove the
  "not implemented yet" caveat from the MCP README.
  - depends: P1-T02

- [x] **P1-T10** — Wire real `retry_failed_run`.
  - depends: P1-T03

- [x] **P1-T11** — Add MCP tools `cancel_run`, `backfill_asset`,
  `list_partitions`.
  - depends: P1-T04, P1-T05, P1-T06

- [x] **P1-T12** — Add MCP prompts `phlo.debug_run`,
  `phlo.triage_failure`, `phlo.audit_asset`, `phlo.plan_backfill`,
  `phlo.scaffold_workflow`.
  - Files: `packages/phlo-mcp/src/phlo_mcp/prompts.py` (new)
  - depends: none

- [x] **P1-T13** — Extend
  [`smoke_stack.py`](../../packages/phlo-mcp/tests/smoke_stack.py) with
  `--exercise-live-write-tools` flag that materialises a no-op asset.
  - depends: P1-T09..T11

- [x] **P1-T14** — Split off ADR
  `docs/plans/2026-05-28-002-lakehouse-operate-scope.md` capturing the
  scope-model decision.
  - depends: P1-T08

### Phase 2 — Author + validate loop

- [x] **P2-T01** — De-interactive `phlo workflow create`: split into pure
  `_create_workflow(...)` + Click wrapper.
  - Files: [`src/phlo/cli/commands/workflow.py`](../../src/phlo/cli/commands/workflow.py)
  - depends: none

- [x] **P2-T02** — De-interactive `phlo plugin scaffold` and any other
  `click.prompt`-using scaffolder.
  - Files: [`src/phlo/cli/commands/plugin/scaffold.py`](../../src/phlo/cli/commands/plugin/scaffold.py)
  - depends: none

- [x] **P2-T03** — Extract `phlo doctor` diagnostic engine into a pure
  library function callable without Click.
  - Files: split [`src/phlo/cli/commands/doctor.py`](../../src/phlo/cli/commands/doctor.py)
    into `phlo.doctor` (lib) + thin CLI
  - depends: none

- [x] **P2-T04** — Add `project:write` scope to authz model.
  - depends: P1-T08

- [x] **P2-T05** — `POST /api/authoring/workflows` route in `phlo-api`.
  - Files: `packages/phlo-api/src/phlo_api/api/authoring.py` (new)
  - depends: P2-T01, P2-T04

- [x] **P2-T06** — `POST /api/authoring/workflows/validate` route.
  - depends: P2-T04

- [x] **P2-T07** — `POST /api/authoring/schemas/validate` route.
  - depends: P2-T04

- [x] **P2-T08** — `GET /api/authoring/templates` route.
  - depends: P2-T04

- [x] **P2-T09** — `GET /api/authoring/workflows` route.
  - depends: P2-T04

- [x] **P2-T10** — `POST /api/authoring/project/lint` route.
  - depends: P2-T03, P2-T06

- [x] **P2-T11** — `GET /api/doctor` route wrapping the extracted engine.
  - depends: P2-T03

- [x] **P2-T12** — MCP tools: `create_workflow`, `validate_workflow`,
  `validate_schema`.
  - depends: P2-T05..T07

- [x] **P2-T13** — MCP tools: `list_workflows`, `list_templates`,
  `lint_project`, `run_doctor`.
  - depends: P2-T08..T11

- [x] **P2-T14** — MCP search tools: `search_assets`, `search_contracts`,
  `search_runs` (server-side filter; pagination shape stubbed for Phase 3).
  - Files: extend `packages/phlo-api/src/phlo_api/api/observatory_api/`
    with search params; add MCP tool wrappers
  - depends: none

### Phase 3 — Agent ergonomics

- [x] **P3-T01** — Create `packages/phlo-mcp/src/phlo_mcp/models.py` with
  Pydantic response models for every existing MCP tool.
  - depends: none

- [x] **P3-T02** — Pass `output_schema=Model.model_json_schema()` on every
  `@mcp.tool()` decorator; add contract test asserting presence.
  - Files: [`server.py`](../../packages/phlo-mcp/src/phlo_mcp/server.py),
    `tests/test_models.py` (new)
  - depends: P3-T01

- [x] **P3-T03** — Align `phlo-api` `response_model=` on every route to the
  same shapes.
  - depends: P3-T01

- [x] **P3-T04** — Cursor-pagination contract: opaque base64 cursor type,
  helper module, and one reference route (`get_recent_alerts`).
  - Files: `packages/phlo-api/src/phlo_api/pagination.py` (new)
  - depends: none

- [x] **P3-T05** — Apply cursor pagination to remaining list/search
  routes: `get_materialization_history`, `get_run_logs`, `get_trace_spans`,
  `list_workflows`, `search_*`, asset list.
  - depends: P3-T04

- [x] **P3-T06** — `PhloMcpError` class + mapping table for common HTTP
  status / capability errors.
  - Files: `packages/phlo-mcp/src/phlo_mcp/errors.py` (new),
    update [`api_client.py`](../../packages/phlo-mcp/src/phlo_mcp/api_client.py)
  - depends: none

- [x] **P3-T07** — Convert MCP tool results to return structured error
  objects (not raise) when the call fails, with rendered text fallback.
  - depends: P3-T06

- [x] **P3-T08** — Extend `GET /api/loki/runs/{run_id}` with `query`,
  `regex`, `since`, `until`, `cursor`.
  - depends: P3-T04

- [x] **P3-T09** — `GET /api/loki/runs/{run_id}/stream` (SSE).
  - depends: none

- [x] **P3-T10** — MCP tools `search_run_logs`, `follow_run_logs`
  (bounded streamable-http).
  - depends: P3-T08, P3-T09

- [x] **P3-T11** — `GET /api/observatory/v2/quality-results` route and
  `get_quality_results` MCP tool.
  - depends: none

- [x] **P3-T12** — `GET /api/observatory/v2/lineage/{asset_key}` route
  (upstream/downstream/both, depth) and `get_lineage` MCP tool.
  - depends: none

- [x] **P3-T13** — `POST /api/observatory/v2/schemas/diff` route and
  `diff_schema` MCP tool (wraps `schema-migrate diff`).
  - depends: none

- [x] **P3-T14** — Self-introspection resources `phlo://docs/cli`,
  `phlo://docs/mcp/tools`, `phlo://docs/mcp/prompts` generated at server
  start.
  - Files: extend
    [`server.py`](../../packages/phlo-mcp/src/phlo_mcp/server.py)
  - depends: P3-T02 (for tool schemas)

### Phase 4 — Discoverability + safety

- [x] **P4-T01** — Scaffold `src/phlo/cli/commands/mcp/` group with
  `serve`, `install`, `tools`, `prompts`, `config` subcommands.
  - depends: none

- [x] **P4-T02** — `phlo mcp serve` wraps existing
  [`phlo-mcp` entrypoint](../../packages/phlo-mcp/src/phlo_mcp/cli.py);
  console script stays as alias for one minor.
  - depends: P4-T01

- [x] **P4-T03** — `phlo mcp install <client>` writes config block for
  `claude-code`, `amp`, `cursor`, `vscode`; supports `--dry-run`.
  - depends: P4-T01

- [x] **P4-T04** — Shared
  `phlo.cli.output.json_envelope(data, warnings, errors)` helper.
  - Files: [`src/phlo/cli/output.py`](../../src/phlo/cli/output.py)
  - depends: none

- [x] **P4-T05** — Add `--json` to read-heavy commands:
  `services list/status`, `catalog tables`, `lineage show`, `status`,
  `workflow check`, `contracts list`, `plugin list/info`, `schema list`.
  - depends: P4-T04

- [x] **P4-T06** — Add `--json` to mutator commands; emit per-action JSON
  line on success/failure.
  - depends: P4-T04

- [x] **P4-T07** — Add global `--quiet` / `--no-color` flags wired through
  [`main.py`](../../src/phlo/cli/main.py).
  - depends: none

- [x] **P4-T08** — Implement token scope claims (`lakehouse:read`,
  `lakehouse:operate`, `project:write`, `admin`); enforce per-route.
  - depends: P1-T08, P2-T04

- [x] **P4-T09** — Document scopes in
  [auth-and-access](../reference/auth-and-access.md) and update
  [phlo-mcp README](../../packages/phlo-mcp/README.md) with required-scope
  column per tool.
  - depends: P4-T08

- [x] **P4-T10** — Append JSONL audit records for every write call to
  `.phlo/audit/operations.jsonl` (or configured sink).
  - Files: `packages/phlo-api/src/phlo_api/audit.py` (new)
  - depends: P1-T02..T05

- [x] **P4-T11** — `phlo audit tail` and `phlo audit query` CLI.
  - Files: `src/phlo/cli/commands/audit.py` (new)
  - depends: P4-T10

- [x] **P4-T12** — Audit-log rotation (size + time) and retention docs.
  - depends: P4-T10

- [x] **P4-T13** — Per-token token-bucket rate limits on mutation routes
  with documented defaults and override.
  - Files: `packages/phlo-api/src/phlo_api/rate_limit.py` (new)
  - depends: P1-T02..T05

- [x] **P4-T14** — `AGENTS.md` template in `csv-batch` starter.
  - Files: `src/phlo/cli/templates/csv_batch/AGENTS.md.jinja`
  - depends: P2-T13 (so tools referenced exist)

- [x] **P4-T15** — `AGENTS.md` in `rest-api`, `dbt-medallion`, `sling`,
  `observatory-demo` starters.
  - depends: P4-T14

- [x] **P4-T16** — Add `AGENTS.md` section to the project
  [AGENTS.md](../../AGENTS.md) covering contributor workflows around the
  new tools.
  - depends: P4-T14

### Cross-phase / housekeeping

- [x] **X-T01** — Update [CLI Reference](../reference/cli-reference.md) at
  the end of each phase.
- [x] **X-T02** — Update [phlo-mcp README](../../packages/phlo-mcp/README.md)
  at the end of each phase.
- [x] **X-T03** — Add a `CHANGELOG.md` entry per merged task.
- [x] **X-T04** — On Phase 4 completion, update the `status:` frontmatter of
  this plan to `completed` and fill in the **Outcome** section.

## Appendix C — Out of scope (parking lot)

- Multi-stack / multi-tenant MCP federation.
- Long-running tool calls > 60s (would need MCP progress notifications).
- Notebook authoring tools (Jupyter, marimo).
- LLM-mediated SQL generation against Trino (`phlo-trino` concern).
- A "phlo-agent" of our own — Phlo provides the surface; agents are the
  client's choice.
