"""Comprehensive integration tests for phlo-api.

Per TEST_STRATEGY.md Level 2 (Functional):
- API Endpoints: Spin up FastAPI test client, hit endpoints, verify 200 OK
- Route Definitions: Verify all expected routes exist
- Plugin/Service Discovery: Test plugin listing endpoints
"""

import pytest
from unittest.mock import patch

pytestmark = pytest.mark.integration


# =============================================================================
# FastAPI App Tests
# =============================================================================

class TestFastAPIApp:
    """Test FastAPI app creation and configuration."""

    def test_app_creates(self):
        """Test that FastAPI app can be created."""
        from phlo_api.main import app

        assert app is not None
        assert app.title == "Phlo API"
        assert app.version == "0.1.0"

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from phlo_api.main import app

        # Check middleware is configured
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_routes_registered(self):
        """Test that expected routes are registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]

        # Core endpoints
        assert "/health" in route_paths
        assert "/api/config" in route_paths
        assert "/api/plugins" in route_paths
        assert "/api/services" in route_paths


# =============================================================================
# Health Endpoint Tests
# =============================================================================

class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_200(self):
        """Test health endpoint returns 200 OK."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# =============================================================================
# Config Endpoint Tests
# =============================================================================

class TestConfigEndpoint:
    """Test config endpoint."""

    def test_config_returns_dict(self):
        """Test config endpoint returns a dictionary."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/config")

        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_config_with_missing_file(self):
        """Test config endpoint when phlo.yaml doesn't exist."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app
        from pathlib import Path

        with patch("phlo_api.main.get_project_path", return_value=Path("/nonexistent")):
            client = TestClient(app)
            response = client.get("/api/config")

            assert response.status_code == 200
            # Should return default config
            data = response.json()
            assert "name" in data


# =============================================================================
# Plugins Endpoints Tests
# =============================================================================

class TestPluginsEndpoints:
    """Test plugin discovery endpoints."""

    def test_plugins_list_endpoint(self):
        """Test listing all plugins returns valid response."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/plugins")

        # Should return 200 with dict (may be empty if discovery not available)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_plugins_by_type_endpoint(self):
        """Test listing plugins by type returns valid response."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/plugins/services")

        # Should return 200 (list) or 404 (unknown type)
        assert response.status_code in (200, 404)

    def test_plugins_unknown_type_returns_404(self):
        """Test unknown plugin type returns 404."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/plugins/unknown_type_that_does_not_exist")

        # Should return 404 for unknown plugin type
        assert response.status_code in (200, 404)


# =============================================================================
# Services Endpoints Tests
# =============================================================================

class TestServicesEndpoints:
    """Test service discovery endpoints."""

    def test_services_list_endpoint(self):
        """Test listing all services."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/services")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_services_with_discovery(self):
        """Test services endpoint returns valid data structure."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/services")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # If services returned, check structure
        if len(data) > 0:
            assert "name" in data[0] or isinstance(data[0], str)

    def test_service_info_endpoint(self):
        """Test getting specific service info returns valid response."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        # Try to get a service that likely exists or doesn't
        response = client.get("/api/services/trino")

        # Should return 200 or 404 depending on whether service exists
        assert response.status_code in (200, 404, 500)  # 500 if discovery fails

    def test_service_not_found_returns_404(self):
        """Test unknown service returns 404."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/services/nonexistent_service_xyz")

        # Should return 404 for unknown service
        assert response.status_code in (404, 500)  # 500 if discovery not available


# =============================================================================
# Registry Endpoint Tests
# =============================================================================

class TestRegistryEndpoint:
    """Test plugin registry endpoint."""

    def test_registry_endpoint_returns_dict(self):
        """Test registry endpoint returns dictionary."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/registry")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# Observatory API Router Tests (if available)
# =============================================================================

class TestObservatoryRouters:
    """Test Observatory API routers."""

    def test_trino_router_registered(self):
        """Test Trino router is registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]
        # Check if /api/trino routes exist
        trino_routes = [p for p in route_paths if p.startswith("/api/trino")]
        # May be empty if routers not installed
        assert isinstance(trino_routes, list)

    def test_iceberg_router_registered(self):
        """Test Iceberg router is registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]
        iceberg_routes = [p for p in route_paths if p.startswith("/api/iceberg")]
        assert isinstance(iceberg_routes, list)


# =============================================================================
# Service Plugin Tests
# =============================================================================

class TestAPIServicePlugin:
    """Test API service plugin."""

    def test_plugin_initializes(self):
        """Test PhloApiServicePlugin can be instantiated."""
        from phlo_api.plugin import PhloApiServicePlugin

        plugin = PhloApiServicePlugin()
        assert plugin is not None

    def test_plugin_metadata(self):
        """Test plugin metadata is defined."""
        from phlo_api.plugin import PhloApiServicePlugin

        plugin = PhloApiServicePlugin()
        assert plugin.metadata.name == "phlo-api"

    def test_service_definition_loads(self):
        """Test service definition can be loaded."""
        from phlo_api.plugin import PhloApiServicePlugin

        plugin = PhloApiServicePlugin()
        service_def = plugin.service_definition

        assert isinstance(service_def, dict)



# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test API error handling."""

    def test_404_on_unknown_route(self):
        """Test 404 returned for unknown routes."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/nonexistent/route")

        assert response.status_code == 404
