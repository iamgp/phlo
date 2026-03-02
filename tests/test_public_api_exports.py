"""Regression tests for public API exports."""

from __future__ import annotations

import importlib
import sys
import types

import pytest

pytestmark = pytest.mark.core_regression


def test_quality_module_populates_exports_on_discovered_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discovered quality providers must hydrate all public exports."""
    provider_package_name = "fake_quality_provider_pkg"
    provider_module_name = f"{provider_package_name}.plugin"

    class _DummyCheck:
        pass

    class _DummyContract:
        pass

    def _get_quality_checks() -> list[str]:
        return ["check"]

    def _clear_quality_checks() -> None:
        return None

    def _dbt_check_name(test_type: str, target: str) -> str:
        return f"{test_type}_{target}"

    provider_package = types.ModuleType(provider_package_name)
    provider_package.get_quality_checks = _get_quality_checks
    provider_package.clear_quality_checks = _clear_quality_checks
    provider_package.CustomSQLCheck = _DummyCheck
    provider_package.QualityCheckContract = _DummyContract
    provider_package.PANDERA_CONTRACT_CHECK_NAME = "pandera_contract"
    provider_package.dbt_check_name = _dbt_check_name

    provider_plugin_module = types.ModuleType(provider_module_name)

    monkeypatch.setitem(sys.modules, provider_package_name, provider_package)
    monkeypatch.setitem(sys.modules, provider_module_name, provider_plugin_module)
    monkeypatch.delitem(sys.modules, "phlo.quality", raising=False)

    class _Provider:
        __module__ = provider_module_name

        def get_decorator(self):
            return lambda fn: fn

        def get_check_classes(self) -> dict[str, type]:
            return {
                "null": _DummyCheck,
                "range": _DummyCheck,
                "freshness": _DummyCheck,
                "unique": _DummyCheck,
                "count": _DummyCheck,
                "schema": _DummyCheck,
                "pattern": _DummyCheck,
                "quality_check": _DummyCheck,
            }

        def get_reconciliation_checks(self) -> dict[str, type]:
            return {
                "reconciliation": _DummyCheck,
                "aggregate_consistency": _DummyCheck,
                "aggregate_spec": _DummyCheck,
                "key_parity": _DummyCheck,
                "multi_aggregate": _DummyCheck,
                "checksum": _DummyCheck,
            }

    import phlo.plugins.discovery as discovery

    monkeypatch.setattr(discovery, "discover_plugins", lambda: None)
    monkeypatch.setattr(discovery, "get_quality_provider", lambda _name: _Provider())

    quality_module = importlib.import_module("phlo.quality")

    assert callable(quality_module.get_quality_checks)
    assert callable(quality_module.clear_quality_checks)
    assert quality_module.get_quality_checks() == ["check"]
    assert quality_module.QualityCheck is _DummyCheck
    assert quality_module.CustomSQLCheck is _DummyCheck
    assert quality_module.QualityCheckContract is _DummyContract
    assert quality_module.PANDERA_CONTRACT_CHECK_NAME == "pandera_contract"
    assert callable(quality_module.dbt_check_name)
    assert quality_module.dbt_check_name("dbt", "users") == "dbt_users"


def test_plugins_module_reexports_provider_getters() -> None:
    """phlo.plugins should expose provider getter helpers."""
    import phlo.plugins as plugins
    import phlo.plugins.discovery as discovery

    assert "get_ingestion_provider" in plugins.__all__
    assert "get_transformation_provider" in plugins.__all__
    assert plugins.get_ingestion_provider is discovery.get_ingestion_provider
    assert plugins.get_transformation_provider is discovery.get_transformation_provider
