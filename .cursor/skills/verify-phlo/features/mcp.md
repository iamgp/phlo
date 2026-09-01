# MCP

A user inspects and serves the Phlo MCP server. Workspace plugin `mcp` registers `phlo mcp`. Read commands do not need Docker; they may still call phlo-api URLs when tools run.

## Sub-features

- `mcp-config` — `--json` envelope; secrets redacted (`api_token` is `***` when set).
- `mcp-tools` / `mcp-prompts` — `--json` lists `name` + `description`.
- `mcp-install` — `install CLIENT --dry-run --json` writes client config unless dry-run.
- `mcp-serve` — `--transport stdio|streamable-http --api-base-url --api-token --enable-write-tools --host --port --path` (long-running).

## How to get to it (user POV)

- `phlo mcp --help`
- `phlo mcp config --json`
- `phlo mcp tools --json`
- `phlo mcp prompts --json`
- `phlo mcp serve --transport stdio`
- `phlo mcp install cursor --dry-run --json`

## Driving it with CLI

Preconditions:

- `phlo-mcp` installed (workspace). Missing extra deps: `MCP support is not installed. Install it with: uv pip install "phlo-mcp"`.

- Tools JSON: `uv run --locked phlo mcp tools --json` → exit 0; envelope `data` is a list including `get_platform_health`, `list_plugins`, `get_service_status`.
- Config JSON: `uv run --locked phlo mcp config --json` → `data.transport`, `data.host`, `data.port`; token redacted.
- Serve is a process: start only if proving it, then kill **that PID**.

## Gotchas

- Tools describe phlo-api; listing tools does not prove the API is up.
- `--enable-write-tools` is a mutation surface; default inspect is read tools.
