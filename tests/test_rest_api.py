"""
Automated tests for Cascade REST API.

Tests authentication, endpoints, and error handling.
"""

import requests
import pytest
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


class TestAuthentication:
    """Test authentication endpoints."""

    def test_login_admin_success(self):
        """Test successful login with admin credentials."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_login_analyst_success(self):
        """Test successful login with analyst credentials."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "analyst", "password": "analyst123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "analyst"
        assert data["user"]["role"] == "analyst"

    def test_login_invalid_username(self):
        """Test login with invalid username."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "invalid", "password": "admin123"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_username(self):
        """Test login with missing username."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"password": "admin123"},
        )
        assert response.status_code == 422

    def test_login_missing_password(self):
        """Test login with missing password."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin"},
        )
        assert response.status_code == 422


class TestProtectedEndpoints:
    """Test protected endpoints require authentication."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    @pytest.fixture
    def analyst_token(self) -> str:
        """Get analyst JWT token."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "analyst", "password": "analyst123"},
        )
        return response.json()["access_token"]

    def test_query_endpoint_requires_auth(self):
        """Test that query endpoint requires authentication."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/query",
            json={"query": "SELECT 1", "engine": "postgres"},
        )
        assert response.status_code == 403

    def test_query_endpoint_with_auth(self, admin_token):
        """Test query endpoint with valid auth token."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/query",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": "SELECT 1 as test", "engine": "postgres"},
        )
        # Should not be 403, either 200 or another error
        assert response.status_code != 403

    def test_iceberg_tables_requires_auth(self):
        """Test that iceberg tables endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/iceberg/tables")
        assert response.status_code == 403

    def test_iceberg_tables_with_auth(self, admin_token):
        """Test iceberg tables endpoint with valid auth."""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/iceberg/tables",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Should not be 403
        assert response.status_code != 403


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns service info."""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_metadata_health_with_auth(self):
        """Test metadata health endpoint with authentication."""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = login_response.json()["access_token"]

        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/metadata/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should not be 403
        assert response.status_code != 403


class TestGlucoseEndpoints:
    """Test glucose data endpoints."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    def test_glucose_recent_requires_auth(self):
        """Test glucose recent endpoint requires auth."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/glucose/recent")
        assert response.status_code == 403

    def test_glucose_recent_with_auth(self, admin_token):
        """Test glucose recent endpoint with auth."""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/glucose/recent",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Should not be 403, might be 200 or 404/500 if no data
        assert response.status_code != 403

    def test_glucose_daily_requires_auth(self):
        """Test glucose daily summary requires auth."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/glucose/daily")
        assert response.status_code == 403

    def test_glucose_hourly_requires_auth(self):
        """Test glucose hourly patterns requires auth."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/glucose/hourly")
        assert response.status_code == 403


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint(self):
        """Test request to non-existent endpoint."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/nonexistent")
        assert response.status_code == 404

    def test_invalid_method(self):
        """Test invalid HTTP method on endpoint."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/auth/login")
        assert response.status_code == 405

    def test_malformed_json(self):
        """Test request with malformed JSON."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_invalid_token(self):
        """Test request with invalid JWT token."""
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/iceberg/tables",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
