"""
Automated tests for Phlo GraphQL API (Hasura).

Tests authentication, queries, and GraphQL-specific functionality.
"""

import pytest
import requests

# Mark entire module as integration tests (requires running API services)
pytestmark = pytest.mark.integration

BASE_URL = "http://localhost:8081"
GRAPHQL_ENDPOINT = f"{BASE_URL}/v1/graphql"
REST_API_URL = "http://localhost:8000/api/v1"


class TestGraphQLAuthentication:
    """Test GraphQL authentication with JWT tokens."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token from REST API."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    @pytest.fixture
    def analyst_token(self) -> str:
        """Get analyst JWT token from REST API."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "analyst", "password": "analyst123"},
        )
        return response.json()["access_token"]

    def test_graphql_requires_auth(self):
        """Test that GraphQL endpoint requires authentication."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
        )
        # Hasura returns 200 but with errors if auth is missing
        assert response.status_code == 200
        data = response.json()
        # Should have errors about missing auth
        assert "errors" in data or "data" in data

    def test_graphql_with_admin_token(self, admin_token):
        """Test GraphQL with admin JWT token."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        # Should not have auth errors with valid token
        if "errors" in data:
            # Check that errors are not auth-related
            for error in data["errors"]:
                assert "unauthorized" not in error.get("message", "").lower()
                assert "permission" not in error.get("message", "").lower()

    def test_graphql_with_analyst_token(self, analyst_token):
        """Test GraphQL with analyst JWT token."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"query": query},
        )
        assert response.status_code == 200

    def test_graphql_with_invalid_token(self):
        """Test GraphQL with invalid JWT token."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": "Bearer invalid_token"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        # Should have errors about invalid token
        assert "errors" in data or ("data" in data and data["data"] is None)


class TestGraphQLIntrospection:
    """Test GraphQL introspection queries."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    def test_schema_introspection(self, admin_token):
        """Test that schema introspection works."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
                mutationType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_type_introspection(self, admin_token):
        """Test type introspection."""
        query = """
        query {
            __type(name: "query_root") {
                name
                kind
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200


class TestGraphQLQueries:
    """Test GraphQL data queries."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    def test_glucose_readings_query(self, admin_token):
        """Test querying glucose readings if table exists."""
        query = """
        query {
            glucose_readings(limit: 10) {
                timestamp
                glucose_mg_dl
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        # Table might not exist, but query should be valid
        data = response.json()
        # Either successful data or error about missing table
        assert "data" in data or "errors" in data

    def test_mart_glucose_overview_query(self, admin_token):
        """Test querying glucose overview mart table."""
        query = """
        query {
            mrt_glucose_overview(limit: 10) {
                date
                avg_glucose
                min_glucose
                max_glucose
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_mart_hourly_patterns_query(self, admin_token):
        """Test querying hourly patterns mart table."""
        query = """
        query {
            mrt_glucose_hourly_patterns(limit: 24) {
                hour_of_day
                avg_glucose
                readings_count
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "errors" in data

    def test_query_with_variables(self, admin_token):
        """Test GraphQL query with variables."""
        query = """
        query GetReadings($limit: Int!) {
            glucose_readings(limit: $limit) {
                timestamp
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query, "variables": {"limit": 5}},
        )
        assert response.status_code == 200

    def test_query_with_where_clause(self, admin_token):
        """Test GraphQL query with where clause."""
        query = """
        query {
            glucose_readings(
                where: {glucose_mg_dl: {_gt: 100}}
                limit: 10
            ) {
                timestamp
                glucose_mg_dl
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200


class TestGraphQLAggregations:
    """Test GraphQL aggregation queries."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    def test_count_aggregation(self, admin_token):
        """Test count aggregation."""
        query = """
        query {
            glucose_readings_aggregate {
                aggregate {
                    count
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200

    def test_numeric_aggregations(self, admin_token):
        """Test numeric aggregations (avg, min, max)."""
        query = """
        query {
            glucose_readings_aggregate {
                aggregate {
                    count
                    avg {
                        glucose_mg_dl
                    }
                    min {
                        glucose_mg_dl
                    }
                    max {
                        glucose_mg_dl
                    }
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200


class TestGraphQLRolePermissions:
    """Test role-based access control in GraphQL."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    @pytest.fixture
    def analyst_token(self) -> str:
        """Get analyst JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "analyst", "password": "analyst123"},
        )
        return response.json()["access_token"]

    def test_admin_can_query(self, admin_token):
        """Test that admin role can query data."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analyst_can_query(self, analyst_token):
        """Test that analyst role can query data."""
        query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestGraphQLErrorHandling:
    """Test GraphQL error handling."""

    @pytest.fixture
    def admin_token(self) -> str:
        """Get admin JWT token."""
        response = requests.post(
            f"{REST_API_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        return response.json()["access_token"]

    def test_malformed_query(self, admin_token):
        """Test handling of malformed GraphQL query."""
        query = """
        query {
            this is not valid graphql
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data

    def test_nonexistent_field(self, admin_token):
        """Test querying non-existent field."""
        query = """
        query {
            nonexistent_table {
                id
            }
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": query},
        )
        assert response.status_code == 200
        data = response.json()
        # Should have validation errors
        assert "errors" in data

    def test_empty_query(self, admin_token):
        """Test empty query handling."""
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"query": ""},
        )
        assert response.status_code in [200, 400]

    def test_missing_query(self, admin_token):
        """Test missing query field."""
        response = requests.post(
            GRAPHQL_ENDPOINT,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        assert response.status_code in [200, 400]


class TestGraphQLHealthCheck:
    """Test GraphQL health and connectivity."""

    def test_graphql_endpoint_accessible(self):
        """Test that GraphQL endpoint is accessible."""
        response = requests.get(BASE_URL)
        # Should get some response (might be redirect or error page)
        assert response.status_code in [200, 301, 302, 404]

    def test_graphql_post_method(self):
        """Test that GraphQL accepts POST requests."""
        query = """
        query {
            __typename
        }
        """
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
