---
title: "ADR: Lakehouse operate scope for agent mutations"
type: adr
status: accepted
date: 2026-05-28
related:
  - docs/plans/2026-05-28-001-agent-first-cli-and-mcp.md
---

# ADR: Lakehouse operate scope for agent mutations

## Decision

Phlo separates read access from mutation access for agent-facing lakehouse
operations. Routes and MCP tools that can launch, retry, cancel, or backfill
runs require `lakehouse:operate`. Project filesystem authoring routes require
`project:write`. `admin` satisfies both checks.

## Consequences

- MCP clients can keep read-only tokens for inspection-heavy workflows.
- Live data-plane operations need an explicit higher-privilege token.
- Operation routes can apply idempotency, audit, and rate limiting at the API
  boundary before calling provider capabilities.
- Scope names are stable API contract terms and are documented in
  `docs/reference/auth-and-access.md`.
