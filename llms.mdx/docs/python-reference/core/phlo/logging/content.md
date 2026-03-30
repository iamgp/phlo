# logging (/docs/python-reference/core/phlo/logging)



Structured logging configuration for Phlo.

This module provides centralized logging infrastructure with structured output
via structlog. It configures both standard library logging and structlog for
consistent, queryable log output across the framework.

Key Features:

* Structured JSON logging for production environments
* Human-readable console output for development
* Automatic sensitive data redaction (passwords, tokens, secrets)
* Correlation context propagation (trace IDs, run IDs, asset keys)
* Hook-based log routing for centralized log aggregation
* Configurable log levels, formats, and output destinations

Main Components:

* :class:`LoggingSettings`: Configuration dataclass for logging
* :func:`setup_logging`: Initialize logging with custom configuration
* :func:`get_logger`: Get a configured structlog logger instance
* :func:`bind_context`: Add context fields to current scope
* :func:`clear_context`: Remove all context fields
* :func:`suppress_log_routing`: Temporarily disable hook bus routing
* :class:`LogRouterHandler`: Routes log records to hook bus

Configuration:
Logging is configured through the :class:`~phlo.config.settings.Settings`
class with the following options:

* `phlo_log_level`: Log level (DEBUG, INFO, WARNING, ERROR)
* `phlo_log_format`: Output format (auto, json, console)
* `phlo_log_router_enabled`: Enable routing to hook bus
* `phlo_log_service_name`: Default service name in logs
* `phlo_log_file_template`: Optional file output path

Sensitive Data Redaction:
The logging system automatically redacts sensitive fields including:

* password, token, secret, authorization, api\_key, apikey
* credential, cookie, bearer

Values are replaced with `\<redacted>` before output.

Correlation Context:
The system maintains correlation fields for distributed tracing:

* request\_id: HTTP request identifier
* trace\_id, span\_id: OpenTelemetry trace context
* run\_id: Dagster run identifier
* asset\_key: Dagster asset key
* job\_name, partition\_key, check\_name: Dagster metadata

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

* :mod:`phlo.config.settings`: Logging configuration settings
* :mod:`phlo.hooks.events.LogEvent`: Log event for hook routing
* structlog documentation: [https://www.structlog.org/](https://www.structlog.org/)

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LoggingSettings&#x22;" href="&#x22;/docs/python-reference/core/phlo/logging/LoggingSettings&#x22;" />

      <Card title="&#x22;LogRouterHandler&#x22;" href="&#x22;/docs/python-reference/core/phlo/logging/LogRouterHandler&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;setup_logging&#x22;" type="&#x22;(settings=None, *, force=False) -> None&#x22;">
      Configure structlog + stdlib logging with configurable output and routing.

      <PySourceCode>
        ```python
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
                    if sys.stdout.isatty()
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

            stream_handler = logging.StreamHandler(sys.stdout)
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;settings&#x22;" type="&#x22;LoggingSettings | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_logger&#x22;" type="&#x22;(name=None, *, service=None) -> structlog.stdlib.BoundLogger&#x22;">
      Return a structlog logger, configuring logging on first use.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;service&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;structlog.structlog.stdlib.structlog.stdlib.BoundLogger&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;log_event&#x22;" type="&#x22;(logger, level, event, **fields) -> None&#x22;">
      Log structured fields when supported, else fallback to a plain message.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Logger instance (structlog or stdlib-like).
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="undefined">
          Log level method name (for example `"info"`).
        </PyParameter>

        <PyParameter name="&#x22;event&#x22;" type="&#x22;str&#x22;" value="undefined">
          Event/message string.
        </PyParameter>

        <PyParameter name="&#x22;fields&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;bind_context&#x22;" type="&#x22;(**fields) -> None&#x22;">
      Bind fields to the current contextvars scope for structured logging.

      <PySourceCode>
        ```python
        def bind_context(**fields: Any) -> None:
            """Bind fields to the current contextvars scope for structured logging."""
            structlog.contextvars.bind_contextvars(**fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;fields&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clear_context&#x22;" type="&#x22;() -> None&#x22;">
      Clear all structlog contextvars fields for the current scope.

      <PySourceCode>
        ```python
        def clear_context() -> None:
            """Clear all structlog contextvars fields for the current scope."""
            structlog.contextvars.clear_contextvars()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_bound_correlation_context&#x22;" type="&#x22;() -> HookCorrelation&#x22;">
      Return the current correlation fields bound in logging contextvars.

      <PySourceCode>
        ```python
        def get_bound_correlation_context() -> HookCorrelation:
            """Return the current correlation fields bound in logging contextvars."""
            values = {
                field: _coerce_optional_string(structlog.contextvars.get_contextvars().get(field))
                for field in _CORRELATION_FIELDS
            }
            return HookCorrelation(**values)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.hooks.events.HookCorrelation&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;suppress_log_routing&#x22;" type="&#x22;() -> Any&#x22;">
      Temporarily disable log routing to the hook bus.

      <PySourceCode>
        ```python
        @contextmanager
        def suppress_log_routing() -> Any:
            """Temporarily disable log routing to the hook bus."""
            token = _ROUTER_ACTIVE.set(True)
            try:
                yield
            finally:
                _ROUTER_ACTIVE.reset(token)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_record_to_event&#x22;" type="&#x22;(record, default_service) -> LogEvent | None&#x22;">
      Convert a log record into a hook `LogEvent`.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;record&#x22;" type="&#x22;logging.LogRecord&#x22;" value="undefined">
          Log record to transform.
        </PyParameter>

        <PyParameter name="&#x22;default_service&#x22;" type="&#x22;str&#x22;" value="undefined">
          Service name used when record extras omit one.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;LogEvent | None&#x22;">
        LogEvent | None: Converted event, or `None` when no message is available.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_extract_message_and_extra&#x22;" type="&#x22;(record) -> tuple[str | None, dict[str, Any]]&#x22;">
      Extract message text and custom extra fields from a log record.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;record&#x22;" type="&#x22;logging.LogRecord&#x22;" value="undefined">
          Log record to inspect.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        tuple\[str | None, dict\[str, Any]]: Normalized message and extra fields.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_metadata&#x22;" type="&#x22;(record, extra) -> dict[str, Any]&#x22;">
      Build metadata payload for a `LogEvent`.

      <PySourceCode>
        ```python
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
            _redact_sensitive_fields(metadata)
            return metadata
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;record&#x22;" type="&#x22;logging.LogRecord&#x22;" value="undefined">
          Source log record.
        </PyParameter>

        <PyParameter name="&#x22;extra&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Additional structured fields from record extras.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, Any]: Metadata dictionary merged with record context.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_redact_sensitive_processor&#x22;" type="&#x22;(_, __, event_dict) -> MutableMapping[str, Any]&#x22;">
      Redact sensitive values from structured event dictionaries.

      <PySourceCode>
        ```python
        def _redact_sensitive_processor(
            _: Any, __: str, event_dict: MutableMapping[str, Any]
        ) -> MutableMapping[str, Any]:
            """Redact sensitive values from structured event dictionaries."""
            _redact_sensitive_fields(event_dict)
            return event_dict
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;_&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;__&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;event_dict&#x22;" type="&#x22;MutableMapping[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.MutableMapping[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_redact_sensitive_fields&#x22;" type="&#x22;(data) -> None&#x22;">
      Redact sensitive keys in-place within a mapping.

      <PySourceCode>
        ```python
        def _redact_sensitive_fields(data: MutableMapping[str, Any]) -> None:
            """Redact sensitive keys in-place within a mapping."""
            for key, value in list(data.items()):
                lowered = key.lower()
                if any(token in lowered for token in _SENSITIVE_FIELD_TOKENS):
                    data[key] = "<redacted>"
                    continue
                if isinstance(value, MutableMapping):
                    _redact_sensitive_fields(value)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;MutableMapping[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_file_handler&#x22;" type="&#x22;(template, formatter) -> logging.Handler | None&#x22;">
      Create a file handler from a template path.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;template&#x22;" type="&#x22;str&#x22;" value="undefined">
          Log path template with date/time placeholders.
        </PyParameter>

        <PyParameter name="&#x22;formatter&#x22;" type="&#x22;logging.Formatter&#x22;" value="undefined">
          Formatter applied to the file handler.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;logging.Handler | None&#x22;">
        logging.Handler | None: Configured file handler, or `None` on template errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_render_log_file_path&#x22;" type="&#x22;(template) -> Path | None&#x22;">
      Render and prepare an absolute log file path from a template.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;template&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path template that may include date/time placeholders.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Path | None&#x22;">
        Path | None: Resolved path with parent directory created, or `None` if invalid.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_pop_tags&#x22;" type="&#x22;(extra) -> dict[str, str]&#x22;">
      Extract normalized string tags from record extras.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;extra&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Extra fields dictionary to consume.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, str]: Tag dictionary with string keys and values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_pop_value&#x22;" type="&#x22;(extra, key) -> str | None&#x22;">
      Pop and stringify a value from extras.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;extra&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
          Extra fields dictionary to consume.
        </PyParameter>

        <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Field name to remove.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;">
        str | None: Stringified value or `None` when absent.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_coerce_optional_string&#x22;" type="&#x22;(value) -> str | None&#x22;">
      Normalize correlation values into optional strings.

      <PySourceCode>
        ```python
        def _coerce_optional_string(value: Any) -> str | None:
            """Normalize correlation values into optional strings."""
            if value is None:
                return None
            return str(value)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_log_level&#x22;" type="&#x22;(level) -> int&#x22;">
      Resolve a log level name to a stdlib numeric level.

      <PySourceCode>
        ```python
        def _coerce_log_level(level: str) -> int:
            """Resolve a log level name to a stdlib numeric level.

            Args:
                level: Log level name.

            Returns:
                int: Numeric logging level.

            """
            return logging._nameToLevel.get(level.upper(), logging.INFO)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="undefined">
          Log level name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;">
        Numeric logging level.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_mark_phlo_handler&#x22;" type="&#x22;(handler) -> None&#x22;">
      Mark a handler as managed by Phlo logging setup.

      <PySourceCode>
        ```python
        def _mark_phlo_handler(handler: logging.Handler) -> None:
            """Mark a handler as managed by Phlo logging setup.

            Args:
                handler: Logging handler to mark.

            """
            setattr(handler, "_phlo_handler", True)  # noqa: B010
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;handler&#x22;" type="&#x22;logging.Handler&#x22;" value="undefined">
          Logging handler to mark.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_remove_phlo_handlers&#x22;" type="&#x22;(root) -> None&#x22;">
      Remove handlers previously attached by Phlo from a logger.

      <PySourceCode>
        ```python
        def _remove_phlo_handlers(root: logging.Logger) -> None:
            """Remove handlers previously attached by Phlo from a logger.

            Args:
                root: Logger from which managed handlers are removed.

            """
            for handler in list(root.handlers):
                if getattr(handler, "_phlo_handler", False):
                    root.removeHandler(handler)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;root&#x22;" type="&#x22;logging.Logger&#x22;" value="undefined">
          Logger from which managed handlers are removed.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
