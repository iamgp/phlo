---
title: "feat: Add guarded phlo-mcp operational tools"
type: plan
status: completed
date: 2026-04-25
origin: PR-468-follow-up
---

# Guarded phlo-mcp Operational Tools

## Overview

Add opt-in MCP tools for safe operational actions such as materializing assets,
retrying failed runs, and checking job status.

## Problem

The current MCP server is read-only. Agents can inspect issues but cannot trigger
the common remediation actions operators expect.

## Requirements

- Keep write tools disabled by default.
- Require explicit `PHLO_MCP_ENABLE_WRITE_TOOLS=true`.
- Require authenticated `phlo-api`.
- Expose dry-run metadata where possible.
- Return structured audit context for every write action.

## Implementation

- Add config flag for write tools.
- Add guarded tool registration in `server.py`.
- Add `PhloApiClient` methods for operation endpoints once stable.
- Add tests that write tools are absent by default and present only when enabled.
- Document safety model and expected auth.

## Verification

```bash
uv run pytest packages/phlo-mcp/tests/test_phlo_mcp.py -q
```

## Outcome

Implemented the MCP-side guard. `PHLO_MCP_ENABLE_WRITE_TOOLS` and
`--enable-write-tools` register `materialize_asset`, `retry_failed_run`, and
`get_dagster_run_status` only when an API token is configured. The mutation tools
default to dry-run mode and return structured `audit_context` metadata without
exposing the token.
