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
- `inspect_materialization`
- `get_asset_materialization_trace`
- `render_materialization_trace_tree`
- `render_run_trace_tree`

Run-level and materialization tools rely on the backing `phlo-api` having access
to Dagster asset history, Loki log queries, and ClickStack OTEL trace storage.

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
- "Render the run trace tree for `abc-123`."

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
uv run python packages/phlo-mcp/tests/smoke_stack.py
```

Use real data assertions when you have a known run or asset:

```bash
uv run python packages/phlo-mcp/tests/smoke_stack.py \
  --run-id abc-123 \
  --require-run-spans \
  --asset-key silver/orders \
  --require-materialization
```
