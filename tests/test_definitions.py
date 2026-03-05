"""Tests for phlo_dagster.framework.definitions."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import dagster as dg
import pytest

from phlo.exceptions import PhloCapabilitySetupError

pytestmark = pytest.mark.integration


@dataclass
class _Settings:
    """Minimal settings stub used to control executor selection in tests."""

    phlo_force_in_process_executor: bool = False
    phlo_force_multiprocess_executor: bool = False
    phlo_host_platform: str | None = None
    phlo_orchestrator: str = "dagster"


def test_default_executor_honors_platform() -> None:
    """Selects executor type from detected platform when no force flags are set."""
    with patch("phlo_dagster.framework.definitions.get_settings", return_value=_Settings()):
        with patch("platform.system", return_value="Darwin"):
            from phlo_dagster.framework.definitions import _default_executor

            executor = _default_executor()
            assert executor is not None
            assert executor.name == "in_process"

        with patch("platform.system", return_value="Linux"):
            from phlo_dagster.framework.definitions import _default_executor

            executor = _default_executor()
            assert executor is not None
            assert executor.name == "multiprocess"


def test_default_executor_honors_force_flags() -> None:
    """Prefers explicit force flags over platform-derived defaults."""
    settings = _Settings(phlo_force_in_process_executor=True)
    with patch("phlo_dagster.framework.definitions.get_settings", return_value=settings):
        from phlo_dagster.framework.definitions import _default_executor

        executor = _default_executor()
        assert executor is not None
        assert executor.name == "in_process"

    settings = _Settings(phlo_force_multiprocess_executor=True)
    with patch("phlo_dagster.framework.definitions.get_settings", return_value=settings):
        from phlo_dagster.framework.definitions import _default_executor

        executor = _default_executor()
        assert executor is not None
        assert executor.name == "multiprocess"


def test_build_definitions_merges_user_defs() -> None:
    """Builds Dagster definitions when workflow discovery returns user definitions."""
    empty_defs = dg.Definitions()
    with (
        patch("phlo_dagster.framework.definitions.get_settings", return_value=_Settings()),
        patch(
            "phlo_dagster.framework.definitions.discover_user_workflows", return_value=empty_defs
        ),
        patch("phlo_dagster.framework.definitions._default_executor", return_value=None),
    ):
        from phlo_dagster.framework.definitions import build_definitions

        result = build_definitions(workflows_path="workflows")
        assert isinstance(result, dg.Definitions)


def test_build_definitions_raises_required_capability_setup_error() -> None:
    with (
        patch("phlo_dagster.framework.definitions.get_settings", return_value=_Settings()),
        patch(
            "phlo_dagster.framework.definitions.discover_user_workflows",
            side_effect=PhloCapabilitySetupError(
                capability="dbt",
                required=True,
                message="dbt asset discovery failed: manifest_unavailable",
            ),
        ),
        patch("phlo_dagster.framework.definitions._default_executor", return_value=None),
    ):
        from phlo_dagster.framework.definitions import build_definitions

        with pytest.raises(PhloCapabilitySetupError, match="manifest_unavailable"):
            build_definitions(workflows_path="workflows")
