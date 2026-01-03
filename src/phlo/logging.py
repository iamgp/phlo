"""
Structured logging helpers for Phlo.

Provides centralized logging setup, a hook-based log router, and
Dagster-aware context helpers.
"""

from __future__ import annotations

import contextvars
import logging
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Mapping, MutableMapping, TypeVar

import structlog

from phlo.config import get_settings
from phlo.hooks import LogEvent, get_hook_bus

if TYPE_CHECKING:
    from dagster import AssetExecutionContext, OpExecutionContext

T = TypeVar("T")

_STANDARD_LOG_RECORD_FIELDS = set(
    logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None)
    .__dict__
    .keys()
)
_CORRELATION_FIELDS = ("run_id", "asset_key", "job_name", "partition_key", "check_name")
_ROUTER_ACTIVE = contextvars.ContextVar("phlo_log_router_active", default=False)
_LOGGING_CONFIGURED = False


@dataclass(frozen=True)
class LoggingSettings:
    level: str = "INFO"
    log_format: str = "json"
    router_enabled: bool = True
    service_name: str = "phlo"

    @classmethod
    def from_settings(cls) -> "LoggingSettings":
        settings = get_settings()
        return cls(
            level=settings.phlo_log_level,
            log_format=settings.phlo_log_format,
            router_enabled=settings.phlo_log_router_enabled,
            service_name=settings.phlo_log_service_name,
        )


def setup_logging(settings: LoggingSettings | None = None, *, force: bool = False) -> None:
    """Configure structlog + stdlib logging with JSON output and routing."""

    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED and not force:
        return

    resolved = settings or LoggingSettings.from_settings()
    level = _coerce_log_level(resolved.level)
    log_format = resolved.log_format.lower()
    service_name = resolved.service_name

    def add_service(_: Any, __: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        event_dict.setdefault("service", service_name)
        return event_dict

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        add_service,
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
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    foreign_pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        add_service,
    ]

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=foreign_pre_chain,
    )

    root = logging.getLogger()
    root.setLevel(level)
    _remove_phlo_handlers(root)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    _mark_phlo_handler(stream_handler)
    root.addHandler(stream_handler)

    if resolved.router_enabled:
        router_handler = LogRouterHandler(service_name=service_name, level=level)
        _mark_phlo_handler(router_handler)
        root.addHandler(router_handler)

    logging.captureWarnings(True)
    _LOGGING_CONFIGURED = True


def get_logger(name: str | None = None, *, service: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger, configuring logging on first use."""

    if not _LOGGING_CONFIGURED:
        setup_logging()
    logger = structlog.get_logger(name)
    if service:
        return logger.bind(service=service)
    return logger


def bind_context(**fields: Any) -> None:
    """Bind fields to the current contextvars scope for structured logging."""

    structlog.contextvars.bind_contextvars(**fields)


def clear_context() -> None:
    """Clear all structlog contextvars fields for the current scope."""

    structlog.contextvars.clear_contextvars()


def dagster_logger(
    context: AssetExecutionContext | OpExecutionContext,
) -> structlog.stdlib.BoundLogger:
    """Return a logger with Dagster correlation fields bound."""

    return get_logger(context.__class__.__module__).bind(**get_correlation_fields(context))


def get_correlation_fields(context: AssetExecutionContext | OpExecutionContext) -> dict[str, Any]:
    """
    Extract correlation fields from Dagster context.

    Returns fields for log correlation:
    - run_id: Dagster run ID
    - asset_key: Asset key path (if available)
    - job_name: Job name
    - partition_key: Partition key (if partitioned)
    """
    fields: dict[str, Any] = {
        "run_id": context.run_id,
    }

    if hasattr(context, "asset_key"):
        fields["asset_key"] = context.asset_key.to_user_string()
    if hasattr(context, "job_name"):
        fields["job_name"] = context.job_name
    if hasattr(context, "partition_key") and context.has_partition_key:
        fields["partition_key"] = context.partition_key

    return fields


def log_with_context(
    context: AssetExecutionContext | OpExecutionContext,
    message: str,
    level: str = "info",
    **extra: Any,
) -> None:
    """Log a message with Dagster correlation fields via context.log."""

    correlation = get_correlation_fields(context)
    all_extra = {**correlation, **extra}

    logger = getattr(context.log, level)
    logger(message, extra=all_extra)


def with_asset_logging(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to add automatic start/end logging with correlation fields."""

    @wraps(func)
    def wrapper(
        context: AssetExecutionContext | OpExecutionContext, *args: Any, **kwargs: Any
    ) -> T:
        correlation = get_correlation_fields(context)

        context.log.info(
            "Asset execution started",
            extra=correlation,
        )

        try:
            result = func(context, *args, **kwargs)
            context.log.info(
                "Asset execution completed",
                extra=correlation,
            )
            return result
        except Exception as exc:
            context.log.error(
                f"Asset execution failed: {exc}",
                extra={**correlation, "error": str(exc)},
            )
            raise

    return wrapper


class LogRouterHandler(logging.Handler):
    """Route log records to the hook bus as LogEvent payloads."""

    def __init__(self, *, service_name: str, level: int = logging.NOTSET) -> None:
        super().__init__(level=level)
        self._service_name = service_name

    def emit(self, record: logging.LogRecord) -> None:
        if _ROUTER_ACTIVE.get():
            return
        token = _ROUTER_ACTIVE.set(True)
        try:
            event = _record_to_event(record, self._service_name)
            if event is None:
                return
            get_hook_bus().emit(event)
        except Exception:
            self.handleError(record)
        finally:
            _ROUTER_ACTIVE.reset(token)


def _record_to_event(record: logging.LogRecord, default_service: str) -> LogEvent | None:
    message, extra = _extract_message_and_extra(record)
    if message is None:
        return None

    service = _pop_value(extra, "service") or default_service
    tags = _pop_tags(extra)
    if service:
        tags.setdefault("service", service)

    correlation = {field: _pop_value(extra, field) for field in _CORRELATION_FIELDS}
    metadata = _build_metadata(record, extra)

    return LogEvent(
        event_type="log.record",
        timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),
        logger=record.name,
        level=record.levelname.lower(),
        message=message,
        service=service,
        run_id=correlation.get("run_id"),
        asset_key=correlation.get("asset_key"),
        job_name=correlation.get("job_name"),
        partition_key=correlation.get("partition_key"),
        check_name=correlation.get("check_name"),
        metadata=metadata,
        tags=tags,
    )


def _extract_message_and_extra(
    record: logging.LogRecord,
) -> tuple[str | None, dict[str, Any]]:
    extra = {
        key: value
        for key, value in record.__dict__.items()
        if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
    }

    event_dict: dict[str, Any] | None = None
    if isinstance(record.msg, Mapping):
        event_dict = dict(record.msg)
    elif isinstance(record.msg, (list, tuple)) and len(record.msg) == 1:
        if isinstance(record.msg[0], Mapping):
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
    metadata = dict(extra)
    metadata.update(
        {
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pathname": record.pathname,
            "process": record.process,
            "thread": record.thread,
        }
    )
    if record.exc_info:
        metadata["exception"] = "".join(traceback.format_exception(*record.exc_info))
    return metadata


def _pop_tags(extra: dict[str, Any]) -> dict[str, str]:
    tags_value = extra.pop("tags", None)
    if isinstance(tags_value, Mapping):
        return {str(key): str(value) for key, value in tags_value.items()}
    return {}


def _pop_value(extra: dict[str, Any], key: str) -> str | None:
    value = extra.pop(key, None)
    if value is None:
        return None
    return str(value)


def _coerce_log_level(level: str) -> int:
    return logging._nameToLevel.get(level.upper(), logging.INFO)


def _mark_phlo_handler(handler: logging.Handler) -> None:
    setattr(handler, "_phlo_handler", True)


def _remove_phlo_handlers(root: logging.Logger) -> None:
    for handler in list(root.handlers):
        if getattr(handler, "_phlo_handler", False):
            root.removeHandler(handler)
