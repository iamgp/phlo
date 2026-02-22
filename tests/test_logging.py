"""Tests for phlo.logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from phlo.logging import (
    LoggingSettings,
    LogRouterHandler,
    _record_to_event,
    _render_log_file_path,
    get_logger,
    log_event,
    setup_logging,
    suppress_log_routing,
)

pytestmark = pytest.mark.core_regression


def _make_record(
    *,
    msg: Any,
    level: int = logging.INFO,
    name: str = "phlo.tests.logging",
    lineno: int = 7,
) -> logging.LogRecord:
    """Create a deterministic `LogRecord` for routing tests."""
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=lineno,
        msg=msg,
        args=(),
        exc_info=None,
        func="test_func",
    )


def test_render_log_file_path_resolves_template(tmp_path: Path) -> None:
    """Resolves ``{YMD}`` placeholders into a concrete log path."""
    template = str(tmp_path / "{YMD}.log")
    path = _render_log_file_path(template)

    assert path is not None
    assert path.parent == tmp_path
    assert path.suffix == ".log"
    assert len(path.stem) == 8


def test_render_log_file_path_respects_project_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resolves relative templates under ``PHLO_PROJECT_PATH`` when set.

    Args:
        tmp_path: Temporary filesystem root for the test.
        monkeypatch: Pytest fixture for environment mutation.
    """
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    template = ".phlo/logs/{YMD}.log"

    path = _render_log_file_path(template)

    assert path is not None
    assert path.parent == tmp_path / ".phlo" / "logs"
    assert path.suffix == ".log"


def test_render_log_file_path_warns_on_unknown_placeholder(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Logs a warning and returns ``None`` for unknown placeholders.

    Args:
        tmp_path: Temporary filesystem root for the test.
        caplog: Pytest fixture for capturing log output.
    """
    template = str(tmp_path / "{NOPE}.log")

    with caplog.at_level(logging.WARNING, logger="phlo.logging"):
        path = _render_log_file_path(template)

    assert path is None
    assert "Unknown log file template placeholder" in caplog.text


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    """Configures file logging and verifies emitted content is persisted.

    Args:
        tmp_path: Temporary filesystem root for the test.
    """
    template = str(tmp_path / "phlo-{YMD}.log")
    settings = LoggingSettings(
        level="INFO",
        log_format="json",
        router_enabled=False,
        service_name="phlo-tests",
        log_file_template=template,
        environment="test",
    )

    setup_logging(settings, force=True)
    logger = get_logger("phlo.tests.logging")
    logger.info("hello file logging", test_case="setup_logging")

    for handler in logging.root.handlers:
        handler.flush()

    path = _render_log_file_path(template)
    assert path is not None
    assert path.exists()
    contents = path.read_text()
    assert "hello file logging" in contents
    assert '"environment": "test"' in contents


def test_setup_logging_redacts_sensitive_fields(tmp_path: Path) -> None:
    """Redacts sensitive values before rendering structured logs."""
    template = str(tmp_path / "redacted-{YMD}.log")
    settings = LoggingSettings(
        level="INFO",
        log_format="json",
        router_enabled=False,
        service_name="phlo-tests",
        log_file_template=template,
        environment="test",
    )

    setup_logging(settings, force=True)
    logger = get_logger("phlo.tests.logging")
    logger.info("sensitive test", api_token="abc123", nested={"password": "p@ss"})

    for handler in logging.root.handlers:
        handler.flush()

    path = _render_log_file_path(template)
    assert path is not None
    assert path.exists()
    contents = path.read_text()
    assert "<redacted>" in contents
    assert "abc123" not in contents
    assert "p@ss" not in contents


def test_record_to_event_extracts_tags_and_metadata() -> None:
    """Builds event fields from record extras and strips consumed keys."""
    record = _make_record(
        msg={
            "event": "asset materialized",
            "service": "ingestion-worker",
            "run_id": 42,
            "asset_key": "raw.orders",
            "tags": {"team": "analytics", "attempt": 2},
            "custom_field": "ok",
            "api_token": "secret-value",
        }
    )

    event = _record_to_event(record, "phlo-default")

    assert event is not None
    assert event.service == "ingestion-worker"
    assert event.message == "asset materialized"
    assert event.run_id == "42"
    assert event.asset_key == "raw.orders"
    assert event.tags == {
        "team": "analytics",
        "attempt": "2",
        "service": "ingestion-worker",
    }
    assert event.metadata["custom_field"] == "ok"
    assert event.metadata["api_token"] == "<redacted>"
    assert "service" not in event.metadata
    assert "run_id" not in event.metadata
    assert "asset_key" not in event.metadata
    assert "tags" not in event.metadata


def test_log_router_handler_emit_routes_and_reports_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Routes converted events and reports failures through `handleError`."""

    class RecordingBus:
        def __init__(self) -> None:
            self.events: list[Any] = []
            self.should_fail = False

        def emit(self, event: Any) -> None:
            if self.should_fail:
                raise RuntimeError("emit failed")
            self.events.append(event)

    bus = RecordingBus()
    monkeypatch.setattr("phlo.hooks.bus.get_hook_bus", lambda: bus)
    handler = LogRouterHandler(service_name="router-service")

    routed = _make_record(msg={"event": "routed", "tags": {"source": "test"}})
    handler.emit(routed)

    assert len(bus.events) == 1
    assert bus.events[0].message == "routed"
    assert bus.events[0].tags["source"] == "test"

    errors: list[logging.LogRecord] = []
    monkeypatch.setattr(handler, "handleError", lambda failed: errors.append(failed))
    bus.should_fail = True
    failing = _make_record(msg="will fail")

    handler.emit(failing)

    assert errors == [failing]


def test_suppress_log_routing_blocks_emit_then_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prevents routing while active and restores routing afterward."""

    class RecordingBus:
        def __init__(self) -> None:
            self.events: list[Any] = []

        def emit(self, event: Any) -> None:
            self.events.append(event)

    bus = RecordingBus()
    monkeypatch.setattr("phlo.hooks.bus.get_hook_bus", lambda: bus)
    handler = LogRouterHandler(service_name="router-service")
    record = _make_record(msg="suppressed check")

    with suppress_log_routing():
        handler.emit(record)

    assert bus.events == []

    handler.emit(record)

    assert len(bus.events) == 1
    assert bus.events[0].message == "suppressed check"


def test_log_event_falls_back_when_logger_rejects_structured_kwargs() -> None:
    """Falls back to plain message formatting on `TypeError`."""

    class LegacyLogger:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def info(self, message: str) -> None:
            self.messages.append(message)

    logger = LegacyLogger()

    log_event(logger, "info", "legacy event", run_id="run-1", attempt=3)

    assert logger.messages == ["legacy event run_id=run-1 attempt=3"]
