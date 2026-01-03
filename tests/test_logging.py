"""Tests for phlo.logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from phlo.logging import LoggingSettings, _render_log_file_path, get_logger, setup_logging


def test_render_log_file_path_resolves_template(tmp_path: Path) -> None:
    template = str(tmp_path / "{YMD}.log")
    path = _render_log_file_path(template)

    assert path is not None
    assert path.parent == tmp_path
    assert path.suffix == ".log"
    assert len(path.stem) == 8


def test_render_log_file_path_respects_project_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    template = ".phlo/logs/{YMD}.log"

    path = _render_log_file_path(template)

    assert path is not None
    assert path.parent == tmp_path / ".phlo" / "logs"
    assert path.suffix == ".log"


def test_render_log_file_path_warns_on_unknown_placeholder(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    template = str(tmp_path / "{NOPE}.log")

    with caplog.at_level(logging.WARNING, logger="phlo.logging"):
        path = _render_log_file_path(template)

    assert path is None
    assert "Unknown log file template placeholder" in caplog.text


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    template = str(tmp_path / "phlo-{YMD}.log")
    settings = LoggingSettings(
        level="INFO",
        log_format="json",
        router_enabled=False,
        service_name="phlo-tests",
        log_file_template=template,
    )

    setup_logging(settings, force=True)
    logger = get_logger("phlo.tests.logging")
    logger.info("hello file logging", test_case="setup_logging")

    for handler in logging.root.handlers:
        handler.flush()

    path = _render_log_file_path(template)
    assert path is not None
    assert path.exists()
    assert "hello file logging" in path.read_text()
