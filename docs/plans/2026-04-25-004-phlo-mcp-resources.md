---
title: "feat: Expose phlo-mcp resources"
type: plan
status: completed
date: 2026-04-25
origin: PR-468-follow-up
---

# phlo-mcp Resources

## Overview

Expose stable MCP resources for docs, package metadata, asset metadata, service status,
and schema contracts.

## Problem

Tools are best for active queries. MCP clients also benefit from navigable resources that
can be read as context without invoking parameterized tools.

## Requirements

- Add resources for package docs and runtime metadata.
- Keep resources read-only.
- Prefer existing `phlo-api` endpoints.
- Use deterministic resource URIs.
- Add tests for resource registration.

## Implementation

- Add resource registration in `server.py`.
- Add API client helpers where needed.
- Document resource URI conventions.
- Add focused MCP server tests.

## Verification

```bash
uv run pytest packages/phlo-mcp/tests/test_phlo_mcp.py -q
```

## Outcome

Implemented read-only MCP resources for runtime config, services, plugins,
assets, schemas, contracts, dashboards, and package docs. Resource URIs are
deterministic and backed by existing `phlo-api` endpoints or local package docs.
