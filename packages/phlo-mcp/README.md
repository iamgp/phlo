# phlo-mcp

MCP server for Phlo observability and lakehouse operations.

## Overview

`phlo-mcp` exposes curated read-only MCP tools over Phlo's observability and
operator surfaces. It sits on top of `phlo-api` and gives MCP clients a stable,
agent-friendly surface for lakehouse inspection.

## Install

```bash
uv pip install -e packages/phlo-mcp
```

## Exposed tools

- `get_platform_health`
- `get_service_status`
- `get_recent_alerts`
- `get_dashboard_links`
- `get_logs_query_link`
- `get_metrics_query_link`
- `get_materialization_history`
- `get_run_logs`
- `get_run_trace_spans`
- `get_trace_spans`
- `render_trace_spans_tree`
- `inspect_materialization`
- `get_asset_materialization_trace`
- `render_materialization_trace_tree`
- `render_run_trace_tree`

Optional guarded operational tools:

- `materialize_asset`
- `retry_failed_run`
- `get_dagster_run_status`

Resources:

- `phlo://runtime/config`
- `phlo://runtime/services`
- `phlo://runtime/services/{service_name}`
- `phlo://runtime/plugins`
- `phlo://runtime/assets`
- `phlo://runtime/assets/{asset_key_path}`
- `phlo://runtime/schemas/{asset_key_path}`
- `phlo://runtime/contracts`
- `phlo://runtime/contracts/{table_name}`
- `phlo://runtime/dashboards`
- `phlo://docs/packages/{package_name}`

Run-level and materialization tools rely on the backing `phlo-api` having access
to Dagster asset history, Loki log queries, and ClickStack OTEL trace storage.
Trace tools can be filtered by run id, asset key, job name, service name, span
name, status code, and start/end time.
Resource URIs are read-only and deterministic so MCP clients can attach Phlo
runtime context without invoking parameterized tools.

When real spans are available, rendered trees include:
- span kind
- status code
- duration
- selected Phlo attributes like stage, asset key, job name, and operation

## Usage

Start a backing API first:

```bash
uv run --package phlo-api uvicorn phlo_api.main:app --host 127.0.0.1 --port 4000
```

Run the MCP server over stdio:

```bash
phlo-mcp --api-base-url http://127.0.0.1:4000
```

For protected `phlo-api` instances, provide a bearer token:

```bash
phlo-mcp \
  --api-base-url http://127.0.0.1:4000 \
  --api-token "$PHLO_API_TOKEN"
```

Guarded operational tools are disabled by default. To expose asset
materialization and run retry tools, set `PHLO_MCP_ENABLE_WRITE_TOOLS=true` or
pass `--enable-write-tools` with an API token. Write tools return structured
`audit_context` metadata and default to `dry_run=true` where supported. Current
`phlo-api` operation routes support dry-run validation and run status; live
Dagster launch and retry are intentionally not implemented yet.

Claude Code example:

```json
{
  "mcpServers": {
    "phlo": {
      "command": "uv",
      "args": ["run", "--package", "phlo-mcp", "phlo-mcp", "--api-base-url", "http://127.0.0.1:4000"]
    }
  }
}
```

Example prompts once connected:

- "Get the latest materializations for `silver/orders`."
- "Fetch logs for run `abc-123`."
- "Inspect the latest materialization for `silver/orders`."
- "Get the latest materialization trace for `silver/orders`."
- "Render the materialization trace tree for `silver/orders`."
- "Get OTEL spans for run `abc-123`."
- "Get failed Dagster spans for asset `silver/orders` in the last hour."
- "Render the run trace tree for `abc-123`."
- "Render a trace tree for job `daily_orders`."

Run it over streamable HTTP:

```bash
phlo-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --path /mcp \
  --api-base-url http://127.0.0.1:4000
```

Optional local span capture:

```bash
phlo-mcp --trace-file .phlo/phlo-mcp-trace.jsonl
```

## Live stack smoke

Run the MCP smoke against live `phlo-api`, Dagster, and ClickStack services:

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py --start-stack
```

The smoke checks live `phlo-api`, Dagster connectivity, ClickStack trace table
queries, MCP tool registration, filtered trace tools, MCP resource registration,
representative MCP resource reads, and a generated `mcp_smoke_asset` fixture.
With `--start-stack`, the fixture is written to `.phlo/mcp-smoke-project`,
which is ignored by git.

When ClickStack requires HTTP credentials, pass them to the smoke script and to
the `phlo-api` process as `CLICKSTACK_QUERY_USER` and
`CLICKSTACK_QUERY_PASSWORD`.

To verify guarded write-tool registration without calling mutation endpoints:

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py \
  --enable-write-tools \
  --api-token "$PHLO_MCP_SMOKE_API_TOKEN"
```

To call guarded write tools in dry-run mode, add `--exercise-write-tools` and
`--start-stack`, or provide `--asset-key` when testing an existing project.
This requires the backing `phlo-api` write endpoints to be available.

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py \
  --start-stack \
  --enable-write-tools \
  --api-token "$PHLO_MCP_SMOKE_API_TOKEN" \
  --exercise-write-tools
```

Use real data assertions when you have a known run or asset:

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py \
  --run-id abc-123 \
  --require-run-spans \
  --asset-key silver/orders \
  --require-materialization
```
