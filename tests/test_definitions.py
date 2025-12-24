"""Tests for phlo.framework.definitions."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import dagster as dg
import pytest

pytestmark = pytest.mark.integration


@dataclass
class _Settings:
    phlo_force_in_process_executor: bool = False
    phlo_force_multiprocess_executor: bool = False
    phlo_host_platform: str | None = None


def test_default_executor_honors_platform() -> None:
    with patch("phlo.framework.definitions.get_settings", return_value=_Settings()):
        with patch("platform.system", return_value="Darwin"):
            from phlo.framework.definitions import _default_executor

            executor = _default_executor()
            assert executor is not None
            assert executor.name == "in_process"

        with patch("platform.system", return_value="Linux"):
            from phlo.framework.definitions import _default_executor

            executor = _default_executor()
            assert executor is not None
            assert executor.name == "multiprocess"


def test_default_executor_honors_force_flags() -> None:
    settings = _Settings(phlo_force_in_process_executor=True)
    with patch("phlo.framework.definitions.get_settings", return_value=settings):
        from phlo.framework.definitions import _default_executor

        executor = _default_executor()
        assert executor is not None
        assert executor.name == "in_process"

    settings = _Settings(phlo_force_multiprocess_executor=True)
    with patch("phlo.framework.definitions.get_settings", return_value=settings):
        from phlo.framework.definitions import _default_executor

        executor = _default_executor()
        assert executor is not None
        assert executor.name == "multiprocess"


def test_build_definitions_merges_user_defs() -> None:
    empty_defs = dg.Definitions()
    with patch("phlo.framework.definitions.get_settings", return_value=_Settings()):
        with patch("phlo.framework.definitions.discover_user_workflows", return_value=empty_defs):
            with patch("phlo.framework.definitions._default_executor", return_value=None):
                from phlo.framework.definitions import build_definitions

                result = build_definitions(workflows_path=\"workflows\")
                assert isinstance(result, dg.Definitions)
