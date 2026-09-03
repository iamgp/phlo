---
title: "test: Add phlo-mcp end-to-end smoke coverage"
type: plan
status: completed
date: 2026-04-25
origin: PR-468-follow-up
---

# phlo-mcp End-to-End Smoke Coverage

## Overview

Add an integration smoke test that starts `phlo-api` and exercises the MCP server against
real HTTP routes.

## Problem

Unit tests verify tool registration and client wrapping, but not the full `phlo-mcp` to
`phlo-api` path.

## Requirements

- Keep the test optional or integration-marked.
- Avoid requiring ClickStack/Dagster for the minimal smoke.
- Verify at least health, dashboard links, and error propagation.
- Run in CI only when dependencies are available.

## Implementation

- Add `@pytest.mark.integration` smoke tests under `packages/phlo-mcp/tests`.
- Start `phlo-api` via ASGI test client or subprocess.
- Use mocked backend providers for deterministic responses.
- Document how to run locally.

## Verification

```bash
uv run pytest packages/phlo-mcp/tests -m integration -q
```

## Outcome

Implemented as `packages/phlo-mcp/tests/smoke_stack.py` with a pytest integration
wrapper at `packages/phlo-mcp/tests/test_stack_smoke.py`. The smoke validates live
`phlo-api`, Dagster connectivity, ClickStack trace-table queries, MCP stdio tool
registration, and representative MCP tool calls. Strict run-span and materialization
assertions can be enabled with `--require-run-spans` and `--require-materialization`.
