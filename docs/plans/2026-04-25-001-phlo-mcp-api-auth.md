---
title: "feat: Add phlo-mcp API authentication"
type: plan
status: completed
date: 2026-04-25
origin: PR-468-follow-up
---

# phlo-mcp API Authentication

## Overview

Allow `phlo-mcp` to call protected `phlo-api` deployments by sending a bearer token on
all upstream API requests.

## Problem

`phlo-mcp` currently assumes `phlo-api` is reachable without authentication. That works
for local development but blocks regulated or proxy-protected deployments.

## Requirements

- Add `PHLO_MCP_API_TOKEN`.
- Add `phlo-mcp --api-token`.
- Attach `Authorization: Bearer <token>` to every `phlo-api` request when configured.
- Do not log or expose the token in tool responses or traces.
- Document CLI and environment configuration.

## Implementation

- Modify `packages/phlo-mcp/src/phlo_mcp/config.py`.
- Modify `packages/phlo-mcp/src/phlo_mcp/cli.py`.
- Modify `packages/phlo-mcp/src/phlo_mcp/api_client.py`.
- Update `packages/phlo-mcp/tests/test_phlo_mcp.py`.
- Update `packages/phlo-mcp/README.md` and `docs/packages/phlo-mcp.md`.

## Verification

```bash
uv run pytest packages/phlo-mcp/tests/test_phlo_mcp.py -q
uv run ruff check packages/phlo-mcp/src/phlo_mcp packages/phlo-mcp/tests/test_phlo_mcp.py
```

## Outcome

Implemented in `phlo-mcp` with `PHLO_MCP_API_TOKEN`, `--api-token`, and bearer-token
request headers.
