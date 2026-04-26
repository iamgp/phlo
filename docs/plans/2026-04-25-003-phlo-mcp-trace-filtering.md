---
title: "feat: Add richer phlo-mcp trace filtering"
type: plan
status: completed
date: 2026-04-25
origin: PR-468-follow-up
---

# phlo-mcp Trace Filtering

## Overview

Extend trace and log inspection with filters for asset, job, status, time window, service,
and span name.

## Problem

Current trace tools are run-id centered. Operators often begin with an asset or failure
window, not a specific run id.

## Requirements

- Filter spans by run id, asset key, job name, service name, status, and time range.
- Keep defaults bounded.
- Preserve current run-id tools.
- Return both raw spans and rendered trees.

## Implementation

- Extend observability backend protocol with filtered trace queries.
- Add ClickStack SQL generation helpers with tests.
- Add `phlo-api` query parameters.
- Add MCP client and server tool wrappers.
- Update docs and examples.

## Verification

```bash
uv run pytest packages/phlo-clickstack/tests packages/phlo-api/tests/test_observability_api.py packages/phlo-mcp/tests/test_phlo_mcp.py -q
```

## Outcome

Implemented filtered trace querying from ClickStack through `phlo-api` and
`phlo-mcp`. Added filters for run id, asset key, job name, service name, span
name, status code, start time, and end time. Existing run-id tools remain, and
new MCP tools return raw spans or rendered span trees.
