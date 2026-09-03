# Logging Guide

Structured logging for Phlo, powered by structlog with automatic hook-bus routing.

## Overview

Phlo wraps [structlog](https://www.structlog.org/) over Python's standard `logging` module
to produce structured, context-rich log output. Every log record can optionally be routed to
the [hook event bus](hook-event-bus.md) as a `LogEvent`, enabling plugins to react to log
activity without coupling to the logging implementation.

## Quick Start

```python
from phlo.logging import get_logger

logger = get_logger(__name__)

logger.info("pipeline started", asset_key="orders", run_id="abc-123")
logger.warning("row count low", count=12)
```

`get_logger()` calls `setup_logging()` automatically the first time it is used, so no
explicit setup is needed in most application code.

## Log Formats

The output format is controlled by `PHLO_LOG_FORMAT`:

| Value     | Behaviour                                                        |
| --------- | ---------------------------------------------------------------- |
| `auto`    | Console (coloured, human-friendly) when stdout is a TTY; JSON otherwise |
| `json`    | Always JSON                                                      |
| `console` | Always console                                                   |

File output (when enabled) is always JSON regardless of the stream format.

## Configuration

All settings are read from environment variables (or `.phlo/.env` / `.phlo/.env.local`).

| Variable                   | Default              | Description                                     |
| -------------------------- | -------------------- | ----------------------------------------------- |
| `PHLO_LOG_LEVEL`           | `WARNING`            | Minimum log level (`DEBUG`, `INFO`, `WARNING`, …) |
| `PHLO_LOG_FORMAT`          | `auto`               | Output format: `auto`, `json`, or `console`     |
| `PHLO_LOG_ROUTER_ENABLED`  | `true`               | Emit log records to the hook bus as `LogEvent`s  |
| `PHLO_LOG_SERVICE_NAME`    | `phlo`               | Default `service` field on every log record      |
| `PHLO_LOG_FILE_TEMPLATE`   | `.phlo/logs/{YMD}.log` | File path template (empty string to disable)   |

## Context Binding

Attach correlation fields to all subsequent log records in the current async/thread context:

```python
from phlo.logging import bind_context, clear_context

bind_context(run_id="abc-123", asset_key="orders")
logger.info("processing")          # includes run_id and asset_key
clear_context()                    # resets all bound fields
```

### Correlation Fields

The following fields are recognised by the log router and forwarded to `LogEvent`:

- `run_id`
- `asset_key`
- `job_name`
- `partition_key`
- `check_name`

Any other bound fields are included in the `LogEvent.metadata` dict.

## Hook Bus Routing

When `PHLO_LOG_ROUTER_ENABLED` is `true`, a `LogRouterHandler` is attached to the root
logger. It converts every log record into a `LogEvent` and emits it via `get_hook_bus().emit()`.

The handler uses a re-entrancy guard (`suppress_log_routing()`) to prevent infinite loops
when hook handlers themselves produce log output.

### Suppressing Routing

Use the context manager to temporarily disable routing (for example inside a hook handler):

```python
from phlo.logging import suppress_log_routing

with suppress_log_routing():
    logger.info("this message will NOT be sent to the hook bus")
```

## Service-Scoped Loggers

Override the default service name on a per-logger basis:

```python
logger = get_logger("my_module", service="my-service")
logger.info("hello")  # service="my-service" instead of the global default
```

## File Logging

When `PHLO_LOG_FILE_TEMPLATE` is set (non-empty), a `FileHandler` writes JSON-formatted
logs to the rendered path. Parent directories are created automatically.

### Template Placeholders

Use Python `str.format()` syntax in the template:

| Placeholder   | Example        | Description                    |
| ------------- | -------------- | ------------------------------ |
| `{YMD}`       | `20260217`     | Year + month + day             |
| `{YM}`        | `202602`       | Year + month                   |
| `{Y}` / `{YYYY}` | `2026`     | Four-digit year                |
| `{M}` / `{MM}`   | `02`       | Zero-padded month              |
| `{D}` / `{DD}`   | `17`       | Zero-padded day                |
| `{H}`         | `14`           | Zero-padded hour (UTC)         |
| `{HM}`        | `1430`         | Hour + minute                  |
| `{HMS}`       | `143022`       | Hour + minute + second         |
| `{DATE}`      | `2026-02-17`   | ISO date                       |
| `{TIMESTAMP}` | `20260217143022` | Full timestamp               |

### Path Resolution

- Absolute paths are used as-is.
- Relative paths are resolved against `PHLO_PROJECT_PATH` (env var) if set, otherwise the
  current working directory.

```bash
# Write daily logs under the project .phlo directory
PHLO_LOG_FILE_TEMPLATE=".phlo/logs/{YMD}.log"

# Write hourly logs with an absolute path
PHLO_LOG_FILE_TEMPLATE="/var/log/phlo/{DATE}/{H}.log"
```

## Setup

`setup_logging()` is called automatically by the CLI and by `get_logger()` on first use.
To reconfigure logging (for example in tests or custom entry points), pass `force=True`:

```python
from phlo.logging import setup_logging, LoggingSettings

setup_logging(
    LoggingSettings(level="DEBUG", log_format="json", router_enabled=False),
    force=True,
)
```

`LoggingSettings.from_settings()` reads values from the global `phlo.config.settings`
configuration, so environment variables and `.phlo/.env` files are respected automatically.
