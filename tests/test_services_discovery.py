"""Tests for service discovery with plugin services."""

from pathlib import Path

import pytest

from phlo.plugins import PluginMetadata, ServicePlugin
from phlo.plugins.registry import get_global_registry
from phlo.services.discovery import ServiceDiscovery


class DummyServicePlugin(ServicePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_service", version="1.0.0")

    @property
    def service_definition(self) -> dict:
        return {
            "name": "dummy_service",
            "description": "Dummy service",
            "category": "core",
            "default": True,
            "compose": {"image": "dummy:latest"},
        }


@pytest.fixture
def clean_registry():
    registry = get_global_registry()
    registry.clear()
    yield registry
    registry.clear()


def test_service_discovery_includes_plugins(
    clean_registry: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry = get_global_registry()
    registry.register_service(DummyServicePlugin(), replace=True)

    monkeypatch.setattr(
        "phlo.services.discovery.discover_plugins",
        lambda plugin_type, auto_register: None,
    )

    discovery = ServiceDiscovery(services_dir=tmp_path)
    services = discovery.discover()

    assert "dummy_service" in services
    assert services["dummy_service"].category == "core"
