"""Tests for service discovery with plugin services."""

from pathlib import Path

import pytest

from phlo.plugins import PluginMetadata, ServicePlugin
from phlo.discovery import ServiceDefinition, ServiceDiscovery, get_global_registry


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


def test_inline_service_creation() -> None:
    """Test creating a service from inline config."""
    inline_config = {
        "type": "inline",
        "image": "my-registry/api:latest",
        "ports": ["4000:4000", "4001:4001"],
        "environment": {"API_KEY": "secret", "DEBUG": "true"},
        "volumes": ["./data:/data"],
        "depends_on": ["trino", "postgres"],
        "command": ["uvicorn", "main:app"],
        "description": "My custom API",
    }

    service = ServiceDefinition.from_inline("custom-api", inline_config)

    assert service.name == "custom-api"
    assert service.description == "My custom API"
    assert service.category == "custom"
    assert service.default is True
    assert service.image == "my-registry/api:latest"
    assert service.depends_on == ["trino", "postgres"]
    assert service.compose["ports"] == ["4000:4000", "4001:4001"]
    assert service.compose["environment"] == {"API_KEY": "secret", "DEBUG": "true"}
    assert service.compose["volumes"] == ["./data:/data"]
    assert service.compose["command"] == ["uvicorn", "main:app"]


def test_inline_service_minimal() -> None:
    """Test inline service with minimal config."""
    minimal_config = {
        "type": "inline",
        "image": "nginx:latest",
    }

    service = ServiceDefinition.from_inline("web-server", minimal_config)

    assert service.name == "web-server"
    assert service.description == "Custom service: web-server"
    assert service.category == "custom"
    assert service.image == "nginx:latest"
    assert service.depends_on == []
    assert service.compose == {}


def test_inline_service_with_build() -> None:
    """Test inline service using build instead of image."""
    build_config = {
        "type": "inline",
        "build": {"context": "./my-app", "dockerfile": "Dockerfile.dev"},
        "ports": ["3000:3000"],
    }

    service = ServiceDefinition.from_inline("my-app", build_config)

    assert service.name == "my-app"
    assert service.build == {"context": "./my-app", "dockerfile": "Dockerfile.dev"}
    assert service.image is None
    assert service.compose["ports"] == ["3000:3000"]
