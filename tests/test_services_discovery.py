"""Tests for service discovery with plugin services."""

from pathlib import Path

import pytest

from phlo.plugins import PluginMetadata, ServicePlugin
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery, get_global_registry


def _write_service_yaml(root: Path, folder: str, name: str) -> None:
    """Write a minimal service definition file for discovery tests."""
    service_file = root / folder / "service.yaml"
    service_file.parent.mkdir(parents=True, exist_ok=True)
    service_file.write_text(
        f"name: {name}\ndescription: {name} service\ncategory: core\n",
        encoding="utf-8",
    )


class DummyServicePlugin(ServicePlugin):
    """Provide a minimal service plugin for discovery tests."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Static metadata for the dummy plugin.
        """
        return PluginMetadata(name="dummy_service", version="1.0.0")

    @property
    def service_definition(self) -> dict:
        """Return the service definition used in tests.

        Returns:
            dict: Service configuration for discovery assertions.
        """
        return {
            "name": "dummy_service",
            "description": "Dummy service",
            "category": "core",
            "default": True,
            "compose": {"image": "dummy:latest"},
        }


@pytest.fixture
def clean_registry():
    """Clear the global registry before and after each test."""
    registry = get_global_registry()
    registry.clear()
    yield registry
    registry.clear()


def test_service_discovery_includes_plugins(
    clean_registry: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ensure discovered services include registered service plugins."""
    registry = get_global_registry()
    registry.register_service(DummyServicePlugin(), replace=True)

    monkeypatch.setattr(
        "phlo.plugins.discovery._service_loading.discover_plugins",
        lambda plugin_type, auto_register: None,
    )

    discovery = ServiceDiscovery(services_dir=tmp_path)
    services = discovery.discover()

    assert "dummy_service" in services
    assert services["dummy_service"].category == "core"


def test_service_discovery_refresh_reloads_stale_cache(
    clean_registry: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify cached discovery remains stale until explicit refresh."""
    monkeypatch.setattr(
        "phlo.plugins.discovery._service_loading.discover_plugins",
        lambda plugin_type, auto_register: None,
    )
    _write_service_yaml(tmp_path, "alpha", "alpha")

    discovery = ServiceDiscovery(services_dir=tmp_path)
    first = discovery.discover()
    assert set(first) == {"alpha"}

    _write_service_yaml(tmp_path, "beta", "beta")

    cached = discovery.discover()
    assert cached is first
    assert set(cached) == {"alpha"}

    refreshed = discovery.discover(refresh=True)
    assert refreshed is not first
    assert set(refreshed) == {"alpha", "beta"}


def test_service_discovery_clear_cache_and_refresh_alias(
    clean_registry: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify cache invalidation API triggers rediscovery."""
    monkeypatch.setattr(
        "phlo.plugins.discovery._service_loading.discover_plugins",
        lambda plugin_type, auto_register: None,
    )
    _write_service_yaml(tmp_path, "alpha", "alpha")

    discovery = ServiceDiscovery(services_dir=tmp_path)
    discovery.discover()

    _write_service_yaml(tmp_path, "beta", "beta")
    discovery.clear_cache()
    cleared_reload = discovery.discover()
    assert set(cleared_reload) == {"alpha", "beta"}

    _write_service_yaml(tmp_path, "gamma", "gamma")
    refreshed = discovery.refresh()
    assert set(refreshed) == {"alpha", "beta", "gamma"}


def test_inline_service_creation() -> None:
    """Test creating a service from inline config."""
    inline_config = {
        "type": "inline",
        "image": "my-registry/api:latest",
        "ports": ["4000:4000", "4001:4001"],
        "environment": {"API_KEY": "secret", "DEBUG": "true"},
        "volumes": ["./data:/data"],
        "mem_limit": "1g",
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
    assert service.compose["mem_limit"] == "1g"
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
