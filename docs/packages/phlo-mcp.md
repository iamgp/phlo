# phlo-mcp

MCP server for Phlo observability and lakehouse operations.

## Overview

`phlo-mcp` exposes curated read-only MCP tools over Phlo runtime surfaces.
It sits on top of `phlo-api`, so an MCP client can inspect a lakehouse without
bespoke per-agent glue.

## Installation

```bash
pip install phlo-mcp
# or
uv pip install -e packages/phlo-mcp
```

## What it exposes

Current tools:

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
- `get_run_status`

These tools call `phlo-api` endpoints and return structured JSON results.

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

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `PHLO_MCP_API_BASE_URL` | `http://127.0.0.1:4000` | Base URL for the backing `phlo-api` instance |
| `PHLO_MCP_API_TOKEN` | unset | Bearer token for authenticated `phlo-api` requests |
| `PHLO_MCP_ENABLE_WRITE_TOOLS` | `false` | Register guarded operational tools when an API token is configured |
| `PHLO_MCP_TRANSPORT` | `stdio` | MCP transport (`stdio` or `streamable-http`) |
| `PHLO_MCP_HOST` | `127.0.0.1` | Bind host for streamable HTTP transport |
| `PHLO_MCP_PORT` | `8000` | Bind port for streamable HTTP transport |
| `PHLO_MCP_HTTP_PATH` | `/mcp` | HTTP path for streamable HTTP transport |
| `PHLO_MCP_TRACE_FILE` | unset | Optional JSONL span sink for local span capture |

## Usage

Start a backing API first:

```bash
uv run --package phlo-api uvicorn phlo_api.main:app --host 127.0.0.1 --port 4000
```

Run the MCP server over stdio:

```bash
phlo-mcp --api-base-url http://127.0.0.1:4000
```

For protected `phlo-api` instances, pass a bearer token:

```bash
phlo-mcp \
  --api-base-url http://127.0.0.1:4000 \
  --api-token "$PHLO_API_TOKEN"
```

Guarded operational tools are disabled by default. To expose tools that can
request asset materialization or run retry through `phlo-api`, set
`PHLO_MCP_ENABLE_WRITE_TOOLS=true` or pass `--enable-write-tools` and provide an
API token. Every write tool returns an `audit_context` with the operation,
target, dry-run state, authenticated state, and backing API URL. Tool calls
default to `dry_run=true` where the operation supports it. Current `phlo-api`
operation routes support dry-run validation and run status; live Dagster launch
and retry are intentionally not implemented yet.

Claude Code config example:

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

Useful prompts once connected:

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

Capture local spans to a file while the server runs:

```bash
phlo-mcp \
  --api-base-url http://127.0.0.1:4000 \
  --trace-file .phlo/phlo-mcp-trace.jsonl
```

## Live stack smoke

Run the MCP smoke against a live `phlo-api` service and its configured capability backends:

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py --start-stack
```

The smoke checks live `phlo-api`, orchestration connectivity, trace filtering
through the observability capability, MCP tool registration, MCP resource
registration, representative MCP resource reads, and a generated
`mcp_smoke_asset` capability fixture.
With `--start-stack`, the fixture is written to `.phlo/mcp-smoke-project`,
which is ignored by git.

When the configured observability backend requires credentials, pass them to
the backing `phlo-api` process with that backend's environment variables.

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

## Related packages

- [phlo-api](phlo-api.md) - backing REST/OpenAPI machine contract
