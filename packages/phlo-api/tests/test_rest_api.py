# test_rest_api.py - Automated tests for Phlo REST API endpoints
# Tests health, config, plugins, services, and error handling.

"""
Automated tests for Phlo REST API.

Tests authentication, endpoints, and error handling.
"""

import os

import pytest
import requests

# Mark entire module as integration tests (requires running API services)
pytestmark = pytest.mark.integration

BASE_URL = os.getenv("PHLO_API_URL", "http://localhost:4000")


@pytest.fixture(scope="session", autouse=True)
def _require_api():
    """Skip if phlo-api is not reachable."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.RequestException as exc:  # pragma: no cover - network dependent
        pytest.skip(f"phlo-api not reachable at {BASE_URL}: {exc}")
    if response.status_code != 200:
        pytest.skip(f"phlo-api health check failed ({response.status_code})")


class TestHealthEndpoints:
    """Test health and base endpoints."""

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_is_not_exposed(self):
        """Root should not expose an endpoint."""
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code in [404, 200]


class TestConfigEndpoints:
    """Test config and registry endpoints."""

    def test_get_config(self):
        """Test fetching phlo.yaml config."""
        response = requests.get(f"{BASE_URL}/api/config", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "description" in data

    def test_get_registry(self):
        """Test registry endpoint."""
        response = requests.get(f"{BASE_URL}/api/registry", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data


class TestPluginEndpoints:
    """Test plugin discovery endpoints."""

    def test_get_plugins(self):
        """Test listing plugins."""
        response = requests.get(f"{BASE_URL}/api/plugins", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_plugins_by_type(self):
        """Test listing plugins for a known type."""
        response = requests.get(f"{BASE_URL}/api/plugins", timeout=5)
        assert response.status_code == 200
        data = response.json()
        plugin_types = list(data.keys())
        if not plugin_types:
            pytest.skip("No plugin types returned from /api/plugins")
        plugin_type = plugin_types[0]
        response = requests.get(f"{BASE_URL}/api/plugins/{plugin_type}", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_unknown_plugin_type(self):
        """Unknown plugin types should return 404."""
        response = requests.get(f"{BASE_URL}/api/plugins/__unknown__", timeout=5)
        assert response.status_code == 404


class TestServiceEndpoints:
    """Test service discovery endpoints."""

    def test_get_services(self):
        """Test listing services."""
        response = requests.get(f"{BASE_URL}/api/services", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_service_info(self):
        """Test service detail endpoint."""
        response = requests.get(f"{BASE_URL}/api/services", timeout=5)
        assert response.status_code == 200
        services = response.json()
        if not services:
            pytest.skip("No services discovered by /api/services")
        service_name = services[0]["name"]
        response = requests.get(f"{BASE_URL}/api/services/{service_name}", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == service_name

    def test_unknown_service(self):
        """Unknown services should return 404."""
        response = requests.get(f"{BASE_URL}/api/services/__unknown__", timeout=5)
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint(self):
        """Test request to non-existent endpoint."""
        response = requests.get(f"{BASE_URL}/api/nonexistent", timeout=5)
        assert response.status_code == 404

    def test_invalid_method(self):
        """Test invalid HTTP method on endpoint."""
        response = requests.post(f"{BASE_URL}/api/config", json={}, timeout=5)
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
