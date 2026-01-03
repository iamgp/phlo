"""Hook plugin for forwarding log events to Highlight.io."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from highlight_io import H

from phlo.config import get_settings
from phlo.hooks import LogEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

logger = logging.getLogger(__name__)


class HighlightHookPlugin(HookPlugin):
    """Forward structured log events to Highlight.io."""

    def __init__(self) -> None:
        self._client: H | None = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="highlightio",
            version="0.1.0",
            description="Highlight.io log export for Phlo",
        )

    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="highlight_logs",
                handler=self._handle_log,
                filters=HookFilter(event_types={"log.record"}),
            )
        ]

    def _handle_log(self, event: Any) -> None:
        if not isinstance(event, LogEvent):
            return
        client = self._get_client()
        if client is None:
            return
        record = _build_log_record(event)
        client.logging_handler.emit(record)

    def _get_client(self) -> H | None:
        settings = get_settings()
        if not _highlight_enabled(
            settings.phlo_highlight_enabled,
            settings.phlo_highlight_project_id,
        ):
            return None
        if not settings.phlo_highlight_project_id:
            logger.warning("Highlight.io enabled but PHLO_HIGHLIGHT_PROJECT_ID is not set")
            return None
        if self._client is None:
            self._client = H(
                project_id=settings.phlo_highlight_project_id,
                otlp_endpoint=settings.phlo_highlight_otlp_endpoint or "",
                instrument_logging=False,
                log_level=_coerce_log_level(settings.phlo_log_level),
                service_name=settings.phlo_highlight_service_name or settings.phlo_log_service_name,
                environment=settings.phlo_highlight_environment or "",
                debug=settings.phlo_highlight_debug,
            )
        return self._client


def _highlight_enabled(flag: bool, project_id: str | None) -> bool:
    if flag:
        return True
    return bool(project_id)


def _build_log_record(event: LogEvent) -> logging.LogRecord:
    level = _coerce_log_level(event.level)
    attributes = _build_attributes(event)
    pathname = str(attributes.get("pathname", ""))
    line = _coerce_line(attributes.get("line"))

    args = {"message": event.message, **_stringify_keys(attributes)}
    record = logging.LogRecord(
        name=event.logger,
        level=level,
        pathname=pathname,
        lineno=line,
        msg="%(message)s",
        args=args,
        exc_info=None,
    )

    if event.timestamp is not None:
        record.created = event.timestamp.timestamp()
        record.msecs = (record.created - int(record.created)) * 1000

    if "module" in attributes:
        record.module = str(attributes["module"])
    if "function" in attributes:
        record.funcName = str(attributes["function"])
    return record


def _build_attributes(event: LogEvent) -> dict[str, Any]:
    attributes: dict[str, Any] = dict(event.metadata)
    if event.tags:
        attributes["tags"] = event.tags
    if event.service:
        attributes["service"] = event.service
    if event.run_id:
        attributes["run_id"] = event.run_id
    if event.asset_key:
        attributes["asset_key"] = event.asset_key
    if event.job_name:
        attributes["job_name"] = event.job_name
    if event.partition_key:
        attributes["partition_key"] = event.partition_key
    if event.check_name:
        attributes["check_name"] = event.check_name
    return attributes


def _stringify_keys(data: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in data.items()}


def _coerce_log_level(level: str) -> int:
    return logging._nameToLevel.get(level.upper(), logging.INFO)


def _coerce_line(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
