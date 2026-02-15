"""Tests for NativeProcessManager."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from phlo.plugins.compose.native import NativeProcess, NativeProcessManager
from phlo.plugins.discovery import ServiceDefinition


def _svc(name: str, dev: dict | None = None, **kwargs) -> ServiceDefinition:
    return ServiceDefinition(
        name=name,
        description=f"{name} service",
        category="core",
        dev=dev if dev is not None else {},
        **kwargs,
    )


class TestCanRunDev:
    def test_returns_true_when_dev_has_command(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        svc = _svc("api", dev={"command": ["npm", "start"]})
        assert mgr.can_run_dev(svc) is True

    def test_returns_false_when_no_dev(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        svc = _svc("postgres")
        assert mgr.can_run_dev(svc) is False

    def test_returns_false_when_dev_has_no_command(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        svc = _svc("api", dev={"environment": {"PORT": "3000"}})
        assert mgr.can_run_dev(svc) is False


class TestExpandEnvVars:
    def test_expands_simple_var(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        result = mgr._expand_env_vars("http://${HOST}:${PORT}", {"HOST": "localhost", "PORT": "3000"})
        assert result == "http://localhost:3000"

    def test_uses_default_when_var_missing(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        result = mgr._expand_env_vars("${HOST:-0.0.0.0}", {})
        assert result == "0.0.0.0"

    def test_prefers_env_value_over_default(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        result = mgr._expand_env_vars("${HOST:-0.0.0.0}", {"HOST": "myhost"})
        assert result == "myhost"

    def test_raises_key_error_for_missing_var_without_default(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        with pytest.raises(KeyError, match="MISSING"):
            mgr._expand_env_vars("${MISSING}/path", {})

    def test_no_substitution_when_no_vars(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        assert mgr._expand_env_vars("plain-string", {}) == "plain-string"


class TestResolvePath:
    def test_replaces_project_root(self) -> None:
        mgr = NativeProcessManager(Path("/my/project"))
        svc = _svc("api")
        result = mgr._resolve_path("{project_root}/dist", svc)
        assert result == Path("/my/project/dist")

    def test_replaces_source_path(self) -> None:
        mgr = NativeProcessManager(Path("/my/project"))
        svc = _svc("api", source_path=Path("/pkg/src"))
        result = mgr._resolve_path("{source_path}/build", svc)
        assert result == Path("/pkg/src/build")

    def test_returns_plain_path_when_no_placeholders(self) -> None:
        mgr = NativeProcessManager(Path("/my/project"))
        svc = _svc("api")
        result = mgr._resolve_path("./dist", svc)
        assert result == Path("./dist")


class TestProcessTracking:
    def test_get_running_services_empty(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        assert mgr.get_running_services() == []

    def test_get_process_returns_none_for_unknown(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        assert mgr.get_process("nonexistent") is None

    def test_stop_unknown_service_returns_false(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        result = asyncio.run(mgr.stop_service("nonexistent"))
        assert result is False

    def test_get_running_services_filters_by_poll(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        running = MagicMock()
        running.poll.return_value = None  # still running
        stopped = MagicMock()
        stopped.poll.return_value = 0  # exited

        mgr._processes["alive"] = NativeProcess(name="alive", process=running)
        mgr._processes["dead"] = NativeProcess(name="dead", process=stopped)

        assert mgr.get_running_services() == ["alive"]

    def test_get_process_returns_process(self) -> None:
        mgr = NativeProcessManager(Path("/tmp"))
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        native = NativeProcess(name="api", process=mock_proc)
        mgr._processes["api"] = native

        assert mgr.get_process("api") is native
        assert mgr.get_process("other") is None
