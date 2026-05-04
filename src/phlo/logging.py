"""Structured logging configuration for Phlo.

This module provides centralized logging infrastructure with structured output
via structlog. It configures both standard library logging and structlog for
consistent, queryable log output across the framework.

Key Features:
    - Structured JSON logging for production environments
    - Human-readable console output for development
    - Automatic sensitive data redaction (passwords, tokens, secrets)
    - Correlation context propagation (trace IDs, run IDs, asset keys)
    - Hook-based log routing for centralized log aggregation
    - Configurable log levels, formats, and output destinations

Main Components:
    - :class:`LoggingSettings`: Configuration dataclass for logging
    - :func:`setup_logging`: Initialize logging with custom configuration
    - :func:`get_logger`: Get a configured structlog logger instance
    - :func:`bind_context`: Add context fields to current scope
    - :func:`clear_context`: Remove all context fields
    - :func:`suppress_log_routing`: Temporarily disable hook bus routing
    - :class:`LogRouterHandler`: Routes log records to hook bus

Configuration:
    Logging is configured through the :class:`~phlo.config.settings.Settings`
    class with the following options:
    - ``phlo_log_level``: Log level (DEBUG, INFO, WARNING, ERROR)
    - ``phlo_log_format``: Output format (auto, json, console)
    - ``phlo_log_router_enabled``: Enable routing to hook bus
    - ``phlo_log_service_name``: Default service name in logs
    - ``phlo_log_file_template``: Optional file output path

Sensitive Data Redaction:
    The logging system automatically redacts sensitive fields including:
    - password, token, secret, authorization, api_key, apikey
    - credential, cookie, bearer

    Values are replaced with ``<redacted>`` before output.

Correlation Context:
    The system maintains correlation fields for distributed tracing:
    - request_id: HTTP request identifier
    - trace_id, span_id: OpenTelemetry trace context
    - run_id: Dagster run identifier
    - asset_key: Dagster asset key
    - job_name, partition_key, check_name: Dagster metadata

Example:
    ```python
    from phlo.logging import get_logger, bind_context, clear_context

    # Get a logger
    logger = get_logger(__name__)

    # Log with structured fields
    logger.info("data_loaded", rows=1000, table="users", duration_ms=452)

    # Bind context for multiple log entries
    bind_context(trace_id="abc-123", run_id="run-456")
    logger.info("processing_started")
    logger.info("processing_completed", records=100)
    clear_context()
    ```

See Also:
    - :mod:`phlo.config.settings`: Logging configuration settings
    - :mod:`phlo.hooks.events.LogEvent`: Log event for hook routing
    - structlog documentation: https://www.structlog.org/

"""

from __future__ import annotations

import contextvars
import logging
import os
import sys
import traceback
from collections.abc import Mapping, MutableMapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from phlo.config import get_settings
from phlo.hooks.events import HookCorrelation, LogEvent

_STANDARD_LOG_RECORD_FIELDS = set(
    logging.LogRecord(
        name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
    ).__dict__.keys()
)
_CORRELATION_FIELDS = (
    "request_id",
    "trace_id",
    "span_id",
    "trace_flags",
    "run_id",
    "asset_key",
    "job_name",
    "partition_key",
    "check_name",
)
_SENSITIVE_FIELD_TOKENS = (
    "password",
    "passwd",
    "token",
    "secret",
    "authorization",
    "api_key",
    "apikey",
    "credential",
    "cookie",
    "bearer",
    "private_key",
    "signing_key",
    "encryption_key",
    "cert",
    "ssh",
    "session_id",
    "session_token",
)
_ROUTER_ACTIVE = contextvars.ContextVar("phlo_log_router_active", default=False)
_LOGGING_CONFIGURED = False


@dataclass(frozen=True)
class LoggingSettings:
    """Configuration values for logging initialization."""

    level: str = "INFO"
    log_format: str = "auto"
    router_enabled: bool = True
    service_name: str = "phlo"
    log_file_template: str | None = None
    environment: str = "dev"

    @classmethod
    def from_settings(cls) -> LoggingSettings:
        """Build logging settings from global application settings.

        Returns:
            LoggingSettings: Logging settings resolved from app configuration.

        """
        settings = get_settings()
        return cls(
            level=settings.phlo_log_level,
            log_format=settings.phlo_log_format,
            router_enabled=settings.phlo_log_router_enabled,
            service_name=settings.phlo_log_service_name,
            log_file_template=settings.phlo_log_file_template,
            environment=settings.phlo_environment,
        )


def setup_logging(settings: LoggingSettings | None = None, *, force: bool = False) -> None:
    """Configure structlog + stdlib logging with configurable output and routing."""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED and not force:
        return

    resolved = settings or LoggingSettings.from_settings()
    level = _coerce_log_level(resolved.level)
    log_format = resolved.log_format.lower()
    service_name = resolved.service_name
    environment_name = resolved.environment

    def add_service(
        _: Any, __: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        """Attach default service metadata to each structured log event."""
        event_dict.setdefault("service", service_name)
        return event_dict

    def add_environment(
        _: Any, __: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        """Attach runtime environment metadata to each structured log event."""
        event_dict.setdefault("environment", environment_name)
        return event_dict

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        add_service,
        add_environment,
        _redact_sensitive_processor,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if log_format == "console":
        stream_renderer = structlog.dev.ConsoleRenderer()
    elif log_format == "auto":
        stream_renderer = (
            structlog.dev.ConsoleRenderer()
            if sys.stderr.isatty()
            else structlog.processors.JSONRenderer()
        )
    else:
        stream_renderer = structlog.processors.JSONRenderer()
    file_renderer = structlog.processors.JSONRenderer()

    foreign_pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        add_service,
        add_environment,
        _redact_sensitive_processor,
    ]

    stream_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            stream_renderer,
        ],
        foreign_pre_chain=foreign_pre_chain,
    )
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            file_renderer,
        ],
        foreign_pre_chain=foreign_pre_chain,
    )

    root = logging.getLogger()
    root.setLevel(level)
    _remove_phlo_handlers(root)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(stream_formatter)
    _mark_phlo_handler(stream_handler)
    root.addHandler(stream_handler)

    if resolved.log_file_template:
        file_handler = _build_file_handler(resolved.log_file_template, file_formatter)
        if file_handler is not None:
            file_handler.setLevel(level)
            _mark_phlo_handler(file_handler)
            root.addHandler(file_handler)

    if resolved.router_enabled:
        router_handler = LogRouterHandler(service_name=service_name, level=level)
        _mark_phlo_handler(router_handler)
        root.addHandler(router_handler)

    logging.captureWarnings(True)
    _LOGGING_CONFIGURED = True


def get_logger(
    name: str | None = None, *, service: str | None = None
) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger, configuring logging on first use."""
    if not _LOGGING_CONFIGURED:
        setup_logging()
    logger = structlog.get_logger(name)
    if service:
        return logger.bind(service=service)
    return logger


def log_event(logger: Any, level: str, event: str, **fields: Any) -> None:
    """Log structured fields when supported, else fallback to a plain message.

    Args:
        logger: Logger instance (structlog or stdlib-like).
        level: Log level method name (for example ``"info"``).
        event: Event/message string.
        **fields: Optional structured fields to attach.

    """
    log_method = getattr(logger, level)
    try:
        log_method(event, **fields)
    except TypeError:
        if fields:
            details = " ".join(f"{key}={value}" for key, value in fields.items())
            log_method(f"{event} {details}")
        else:
            log_method(event)


def bind_context(**fields: Any) -> None:
    """Bind fields to the current contextvars scope for structured logging."""
    structlog.contextvars.bind_contextvars(**fields)


def clear_context() -> None:
    """Clear all structlog contextvars fields for the current scope."""
    structlog.contextvars.clear_contextvars()


def get_bound_correlation_context() -> HookCorrelation:
    """Return the current correlation fields bound in logging contextvars."""
    values = {
        field: _coerce_optional_string(structlog.contextvars.get_contextvars().get(field))
        for field in _CORRELATION_FIELDS
    }
    return HookCorrelation(**values)


@contextmanager
def suppress_log_routing() -> Any:
    """Temporarily disable log routing to the hook bus."""
    token = _ROUTER_ACTIVE.set(True)
    try:
        yield
    finally:
        _ROUTER_ACTIVE.reset(token)


class LogRouterHandler(logging.Handler):
    """Route log records to the hook bus as LogEvent payloads."""

    def __init__(self, *, service_name: str, level: int = logging.NOTSET) -> None:
        """Initialize a router handler for hook-bus log forwarding.

        Args:
            service_name: Default service name for emitted log events.
            level: Minimum log level accepted by this handler.

        """
        super().__init__(level=level)
        self._service_name = service_name

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the hook bus as a structured log event.

        Args:
            record: Standard library log record to route.

        """
        if _ROUTER_ACTIVE.get():
            return
        token = _ROUTER_ACTIVE.set(True)
        try:
            event = _record_to_event(record, self._service_name)
            if event is None:
                return
            from phlo.hooks.bus import get_hook_bus

            get_hook_bus().emit(event)
        except Exception:
            self.handleError(record)
        finally:
            _ROUTER_ACTIVE.reset(token)


def _record_to_event(record: logging.LogRecord, default_service: str) -> LogEvent | None:
    """Convert a log record into a hook `LogEvent`.

    Args:
        record: Log record to transform.
        default_service: Service name used when record extras omit one.

    Returns:
        LogEvent | None: Converted event, or `None` when no message is available.

    """
    message, extra = _extract_message_and_extra(record)
    if message is None:
        return None

    service = _pop_value(extra, "service") or default_service
    tags = _pop_tags(extra)
    if service:
        tags.setdefault("service", service)

    bound_correlation = get_bound_correlation_context()
    correlation_values = {
        field: _pop_value(extra, field) or getattr(bound_correlation, field)
        for field in _CORRELATION_FIELDS
    }
    correlation = HookCorrelation(**correlation_values)
    metadata = _build_metadata(record, extra)
    for field in ("request_id", "trace_id", "span_id", "trace_flags"):
        value = getattr(correlation, field)
        if value is not None:
            metadata[field] = value

    return LogEvent(
        event_type="log.record",
        timestamp=datetime.fromtimestamp(record.created, tz=UTC),
        logger=record.name,
        level=record.levelname.lower(),
        message=message,
        service=service,
        run_id=correlation.run_id,
        asset_key=correlation.asset_key,
        job_name=correlation.job_name,
        partition_key=correlation.partition_key,
        check_name=correlation.check_name,
        metadata=metadata,
        tags=tags,
        correlation=correlation,
    )


def _extract_message_and_extra(
    record: logging.LogRecord,
) -> tuple[str | None, dict[str, Any]]:
    """Extract message text and custom extra fields from a log record.

    Args:
        record: Log record to inspect.

    Returns:
        tuple[str | None, dict[str, Any]]: Normalized message and extra fields.

    """
    extra = {
        key: value
        for key, value in record.__dict__.items()
        if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
    }

    event_dict: dict[str, Any] | None = None
    if isinstance(record.msg, Mapping):
        event_dict = dict(record.msg)
    elif (
        isinstance(record.msg, (list, tuple))
        and len(record.msg) == 1
        and isinstance(record.msg[0], Mapping)
    ):
        event_dict = dict(record.msg[0])

    if event_dict:
        extra.update(event_dict)
        message = str(event_dict.pop("event", ""))
    else:
        message = record.getMessage()

    message = message.strip()
    if not message:
        return None, extra
    extra.pop("event", None)
    extra.pop("level", None)
    extra.pop("timestamp", None)
    extra.pop("logger", None)
    return message, extra


def _build_metadata(record: logging.LogRecord, extra: dict[str, Any]) -> dict[str, Any]:
    """Build metadata payload for a `LogEvent`.

    Args:
        record: Source log record.
        extra: Additional structured fields from record extras.

    Returns:
        dict[str, Any]: Metadata dictionary merged with record context.

    """
    metadata = {
        **extra,
        "module": record.module,
        "function": record.funcName,
        "line": record.lineno,
        "pathname": record.pathname,
        "process": record.process,
        "thread": record.thread,
    }
    if record.exc_info:
        metadata["exception"] = "".join(traceback.format_exception(*record.exc_info))
    redact_sensitive_fields(metadata)
    return metadata


def _redact_sensitive_processor(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Redact sensitive values from structured event dictionaries."""
    redact_sensitive_fields(event_dict)
    return event_dict


def redact_sensitive_fields(data: MutableMapping[str, Any]) -> None:
    """Redact sensitive keys in-place within a mapping."""
    for key, value in list(data.items()):
        lowered = key.lower()
        if any(token in lowered for token in _SENSITIVE_FIELD_TOKENS):
            data[key] = "<redacted>"
            continue
        if isinstance(value, MutableMapping):
            redact_sensitive_fields(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, MutableMapping):
                    redact_sensitive_fields(item)


def _build_file_handler(
    template: str,
    formatter: logging.Formatter,
) -> logging.Handler | None:
    """Create a file handler from a template path.

    Args:
        template: Log path template with date/time placeholders.
        formatter: Formatter applied to the file handler.

    Returns:
        logging.Handler | None: Configured file handler, or `None` on template errors.

    """
    path = _render_log_file_path(template)
    if path is None:
        return None
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(formatter)
    return handler


def _render_log_file_path(template: str) -> Path | None:
    """Render and prepare an absolute log file path from a template.

    Args:
        template: Path template that may include date/time placeholders.

    Returns:
        Path | None: Resolved path with parent directory created, or `None` if invalid.

    """
    now = datetime.now(UTC)
    tokens = {
        "YMD": now.strftime("%Y%m%d"),
        "YM": now.strftime("%Y%m"),
        "Y": now.strftime("%Y"),
        "YYYY": now.strftime("%Y"),
        "M": now.strftime("%m"),
        "MM": now.strftime("%m"),
        "D": now.strftime("%d"),
        "DD": now.strftime("%d"),
        "H": now.strftime("%H"),
        "HM": now.strftime("%H%M"),
        "HMS": now.strftime("%H%M%S"),
        "DATE": now.strftime("%Y-%m-%d"),
        "TIMESTAMP": now.strftime("%Y%m%d%H%M%S"),
    }
    try:
        rendered = template.format(**tokens)
    except KeyError as exc:
        logging.getLogger(__name__).warning(
            "Unknown log file template placeholder: %s",
            exc,
        )
        return None
    path = Path(rendered)
    if not path.is_absolute():
        project_root = os.environ.get("PHLO_PROJECT_PATH")
        base_path = Path(project_root) if project_root else Path.cwd()
        path = base_path / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _pop_tags(extra: dict[str, Any]) -> dict[str, str]:
    """Extract normalized string tags from record extras.

    Args:
        extra: Extra fields dictionary to consume.

    Returns:
        dict[str, str]: Tag dictionary with string keys and values.

    """
    tags_value = extra.pop("tags", None)
    if isinstance(tags_value, Mapping):
        return {str(key): str(value) for key, value in tags_value.items()}
    return {}


def _pop_value(extra: dict[str, Any], key: str) -> str | None:
    """Pop and stringify a value from extras.

    Args:
        extra: Extra fields dictionary to consume.
        key: Field name to remove.

    Returns:
        str | None: Stringified value or `None` when absent.

    """
    value = extra.pop(key, None)
    if value is None:
        return None
    return str(value)


def _coerce_optional_string(value: Any) -> str | None:
    """Normalize correlation values into optional strings."""
    if value is None:
        return None
    return str(value)


def _coerce_log_level(level: str) -> int:
    """Resolve a log level name to a stdlib numeric level.

    Args:
        level: Log level name.

    Returns:
        int: Numeric logging level.

    """
    return logging.getLevelNamesMapping().get(level.upper(), logging.INFO)


def _mark_phlo_handler(handler: logging.Handler) -> None:
    """Mark a handler as managed by Phlo logging setup.

    Args:
        handler: Logging handler to mark.

    """
    setattr(handler, "_phlo_handler", True)  # noqa: B010


def _remove_phlo_handlers(root: logging.Logger) -> None:
    """Remove handlers previously attached by Phlo from a logger.

    Args:
        root: Logger from which managed handlers are removed.

    """
    for handler in list(root.handlers):
        if getattr(handler, "_phlo_handler", False):
            root.removeHandler(handler)
