# Centralized Logging Layer Spec

## Overview

Phlo currently emits logs in multiple ways (stdlib logging, Dagster `context.log`,
ad-hoc telemetry events, and Pino in Observatory). This spec defines a centralized
logging layer for Python packages that standardizes log shape, routes every log
through a middle layer, and supports pluggable observability sinks (Loki/Alloy
by default, with optional Highlight.io integration).

The design keeps logs visible even when optional packages are not installed and
ensures packages can import either a setup function or a logger instance.

## Goals

- Provide a single, consistent logging API across Python packages.
- Standardize log schema and correlation fields across services.
- Route every log through a middle layer that can fan out to multiple sinks.
- Keep default behavior simple: JSON to stdout for Alloy/Loki collection.
- Enable optional sinks via packages (e.g., `phlo-highlightio`).
- Keep compatibility with Dagster `context.log` and stdlib `logging`.

## Non-Goals

- Replacing the existing Loki/Grafana stack or its UI.
- Full distributed tracing (future work; allow trace/span fields).
- Rewriting Observatory logging (align fields only).

## Current State

- Python packages use stdlib `logging.getLogger()` or Dagster `context.log`.
- `src/phlo/logging.py` provides Dagster helpers but is not widely used.
- `phlo-metrics` records hook-based telemetry events to JSONL.
- `phlo-alerting` reacts to telemetry events.
- Observatory (TypeScript) uses Pino and logs to stdout.

Gaps: no centralized configuration, inconsistent fields, no shared routing layer,
no unified integration for external observability tools like Highlight.

## Proposed Architecture

### 1. Core Logging API (phlo core)

Create a core logging module that packages can import:

- `setup_logging(settings: LoggingSettings | None = None) -> None`
- `get_logger(name: str | None = None) -> BoundLogger`
- `bind_context(**fields) -> None` / `clear_context() -> None`
- `dagster_logger(context) -> BoundLogger` (binds correlation fields)

Example usage in packages:

```python
from phlo.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
logger.info("Service started", port=8080)
```

### 2. Standard Log Schema

Every log entry must include these core fields:

- `timestamp` (ISO-8601 UTC)
- `level` (debug/info/warning/error/critical)
- `message`
- `logger` (module/logger name)
- `service` (phlo component name, e.g., `phlo-alerting`)

Correlation fields (from ADR-0028):

- `run_id`
- `asset_key`
- `job_name`
- `partition_key`
- `check_name`

Optional fields:

- `event` (short machine-readable name)
- `tags` (string map)
- `exception` (serialized traceback)
- `trace_id` / `span_id` (future tracing)
- `process` / `thread` / `module` / `function` / `line`

### 3. Middle Layer (Log Router)

Introduce a log router handler that receives every log record and forwards a
normalized `LogEvent` to the hook bus:

```
stdlib logging / structlog
          │
          ▼
  Phlo Log Router (logging.Handler)
          │
          ▼
      HookBus
          │
    ┌─────┼──────────┐
    ▼     ▼          ▼
 stdout  metrics   highlight
 (JSON)  plugin    plugin
```

Implementation details:

- Add `LogEvent` to `phlo.hooks.events` with `event_type="log.record"`.
- Add a `LogRouterHandler` that transforms `LogRecord` -> `LogEvent`.
- Use HookBus to dispatch to installed sink plugins.
- Keep stdout JSON as the default sink for Alloy/Loki.

### 4. Logging Backend Choice

Use `structlog` on top of stdlib `logging`:

- Keeps compatibility with Dagster and third-party libraries.
- Supports structured JSON output with processors.
- Allows a single handler pipeline for routing.

### 5. Highlight.io Integration

Create `packages/phlo-highlightio` that registers a hook plugin:

- Entry point: `phlo.plugins.hooks`.
- Handles `log.record` events.
- Uses Highlight Python SDK to send logs (and optional traces).
- Configuration via `phlo.config.settings` and `.phlo/.env`:
  - `PHLO_HIGHLIGHT_ENABLED`
  - `PHLO_HIGHLIGHT_PROJECT_ID`
  - `PHLO_HIGHLIGHT_ENVIRONMENT`
  - `PHLO_HIGHLIGHT_OTLP_ENDPOINT`
  - `PHLO_HIGHLIGHT_SERVICE_NAME`
  - `PHLO_HIGHLIGHT_DEBUG`

### 6. Configuration

Add logging settings to `phlo.config.settings`:

- `phlo_log_level` (default: INFO)
- `phlo_log_format` (json | console)
- `phlo_log_router_enabled` (default: true)
- `phlo_log_service_name` (default: phlo)
- `phlo_log_file_template` (default: .phlo/logs/{YMD}.log, empty disables)

Supported template placeholders (UTC):

- `{YMD}` / `{YM}` / `{Y}` / `{YYYY}`
- `{M}` / `{MM}` / `{D}` / `{DD}`
- `{H}` / `{HM}` / `{HMS}`
- `{DATE}` (YYYY-MM-DD) / `{TIMESTAMP}` (YYYYMMDDHHMMSS)

Allow overrides via env vars and `.phlo/.env(.local)`.

### 7. Dagster Integration

- Provide `dagster_logger(context)` that binds correlation fields from context.
- Ensure Dagster `context.log` output is still captured by the log router.
- Replace ad-hoc `context.log` usage with `dagster_logger` where possible.

### 8. TypeScript Alignment (Observatory)

- Keep Pino, but align fields to the same schema (`service`, `event`,
  correlation keys) so logs stay consistent across languages.

## Rollout Plan

1. Implement core `phlo.logging` API + `LogRouterHandler` + `LogEvent`.
2. Wire `setup_logging()` into CLI entrypoints and services.
3. Update packages to use `get_logger()` or `setup_logging()`.
4. Add `phlo-highlightio` hook plugin.
5. Update docs and examples.

## Migration & Compatibility

- Continue to honor stdlib `logging` usage; logs will still flow through router.
- Existing telemetry log events remain unchanged; they are separate from
  `log.record` but can be correlated via shared fields.
- Gradually migrate package code to `phlo.logging` helpers.

## Open Questions

- Should `log.record` be emitted for every log level, or only INFO+ by default?
- Should Highlight be enabled automatically when installed, or opt-in via config?
- Do we want to require JSON logs in all environments or allow console output for dev?
