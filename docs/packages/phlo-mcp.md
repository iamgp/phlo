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

These tools call `phlo-api` endpoints and return structured JSON results.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `PHLO_MCP_API_BASE_URL` | `http://127.0.0.1:4000` | Base URL for the backing `phlo-api` instance |
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

## Related packages

- [phlo-api](phlo-api.md) - backing REST/OpenAPI machine contract
- [phlo-otel](phlo-otel.md) - OpenTelemetry emission across Phlo runtime events
- [phlo-clickstack](phlo-clickstack.md) - default all-in-one observability backend
