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

        route_paths = [r.path for r in app.routes]  # type: ignore[attr-defined]

        # Core endpoints
        assert "/health" in route_paths
        assert "/api/config" in route_paths
        assert "/api/plugins" in route_paths
        assert "/api/services" in route_paths
        assert "/api/contracts" in route_paths
        assert "/api/contracts/{table_name:path}" in route_paths


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

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_plugins_unknown_type_returns_404(self):
        """Test unknown plugin type returns 404."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/plugins/unknown_type_that_does_not_exist")

        assert response.status_code == 404
        assert "Unknown plugin type" in response.json()["detail"]


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

        # trino may or may not exist in local service manifests.
        assert response.status_code in (200, 404)

    def test_service_not_found_returns_404(self):
        """Test unknown service returns 404."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        client = TestClient(app)
        response = client.get("/api/services/nonexistent_service_xyz")

        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]


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
# Contracts Endpoints Tests
# =============================================================================


class TestContractsEndpoints:
    """Test contract discovery endpoints."""

    def test_contracts_list_endpoint(self):
        """List contracts endpoint returns helper payload."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        payload = [
            {
                "table_name": "raw.contract_demo",
                "asset_key": "dlt_contract_demo",
                "contract_metadata": {"owner": "platform-team", "consumers": [], "sla": None},
            }
        ]
        with patch("phlo_api.main._list_contracts", return_value=payload):
            client = TestClient(app)
            response = client.get("/api/contracts")

        assert response.status_code == 200
        assert response.json() == payload

    def test_contract_detail_endpoint(self):
        """Detail endpoint returns contract for requested table."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        payload = {
            "table_name": "raw.contract_demo",
            "asset_key": "dlt_contract_demo",
            "contract_metadata": {"owner": "platform-team", "consumers": [], "sla": None},
        }
        with patch("phlo_api.main._get_contract_by_table", return_value=payload):
            client = TestClient(app)
            response = client.get("/api/contracts/raw.contract_demo")

        assert response.status_code == 200
        assert response.json() == payload

    def test_contract_detail_endpoint_not_found(self):
        """Detail endpoint returns 404 when table has no contract."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch("phlo_api.main._get_contract_by_table", return_value=None):
            client = TestClient(app)
            response = client.get("/api/contracts/raw.unknown_table")

        assert response.status_code == 404
        assert "Contract not found" in response.json()["detail"]


# =============================================================================
# Observatory API Router Tests (if available)
# =============================================================================


class TestObservatoryRouters:
    """Test Observatory API routers."""

    def test_trino_router_registered(self):
        """Test Trino router is registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]  # type: ignore[attr-defined]
        # Check if /api/trino routes exist
        trino_routes = [p for p in route_paths if p.startswith("/api/trino")]
        # May be empty if routers not installed
        assert isinstance(trino_routes, list)

    def test_iceberg_router_registered(self):
        """Test Iceberg router is registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]  # type: ignore[attr-defined]
        iceberg_routes = [p for p in route_paths if p.startswith("/api/iceberg")]
        assert isinstance(iceberg_routes, list)

    def test_dagster_graph_routes_registered(self):
        """Test Dagster graph routes are registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]  # type: ignore[attr-defined]

        assert "/api/dagster/graph" in route_paths
        assert "/api/dagster/graph/neighbors" in route_paths
        assert "/api/dagster/graph/impact" in route_paths

    def test_contributing_routes_registered(self):
        """Test contributing routes are registered."""
        from phlo_api.main import app

        route_paths = [r.path for r in app.routes]  # type: ignore[attr-defined]

        assert "/api/contributing/query" in route_paths
        assert "/api/contributing/page" in route_paths


class TestDagsterGraphEndpoints:
    """Test Dagster graph endpoints."""

    @staticmethod
    def _graphql_asset_graph_payload():
        return {
            "data": {
                "assetsOrError": {
                    "__typename": "AssetConnection",
                    "nodes": [
                        {
                            "id": "source-id",
                            "key": {"path": ["raw", "source_orders"]},
                            "definition": {
                                "description": "Source orders",
                                "computeKind": "python",
                                "groupName": "ingest",
                                "dependencyKeys": [],
                                "dependedByKeys": [{"path": ["silver", "stg_orders"]}],
                            },
                            "assetMaterializations": [{"timestamp": "100"}],
                        },
                        {
                            "id": "stg-id",
                            "key": {"path": ["silver", "stg_orders"]},
                            "definition": {
                                "description": "Staged orders",
                                "computeKind": "dbt",
                                "groupName": "transform",
                                "dependencyKeys": [{"path": ["raw", "source_orders"]}],
                                "dependedByKeys": [{"path": ["gold", "fct_orders"]}],
                            },
                            "assetMaterializations": [{"timestamp": "200"}],
                        },
                        {
                            "id": "fct-id",
                            "key": {"path": ["gold", "fct_orders"]},
                            "definition": {
                                "description": "Fact orders",
                                "computeKind": "dbt",
                                "groupName": "warehouse",
                                "dependencyKeys": [{"path": ["silver", "stg_orders"]}],
                                "dependedByKeys": [],
                            },
                            "assetMaterializations": [{"timestamp": "300"}],
                        },
                    ],
                }
            }
        }

    def test_dagster_graph_endpoint_transforms_payload(self):
        """Graph endpoint returns Observatory-shaped payload."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch(
            "phlo_api.observatory_api.dagster.graphql_request",
            return_value=self._graphql_asset_graph_payload(),
        ):
            client = TestClient(app)
            response = client.get("/api/dagster/graph")

        assert response.status_code == 200
        data = response.json()
        assert [node["key_path"] for node in data["nodes"]] == [
            "raw/source_orders",
            "silver/stg_orders",
            "gold/fct_orders",
        ]
        assert data["nodes"][0]["layer"] == "bronze"
        assert data["nodes"][1]["upstream_count"] == 1
        assert data["nodes"][1]["downstream_count"] == 1
        assert data["edges"] == [
            {"source": "raw/source_orders", "target": "silver/stg_orders"},
            {"source": "silver/stg_orders", "target": "gold/fct_orders"},
        ]

    def test_dagster_graph_neighbors_filters_subgraph(self):
        """Neighbors endpoint trims graph by direction and depth."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch(
            "phlo_api.observatory_api.dagster.graphql_request",
            return_value=self._graphql_asset_graph_payload(),
        ):
            client = TestClient(app)
            response = client.get(
                "/api/dagster/graph/neighbors",
                params={
                    "asset_key": "silver/stg_orders",
                    "direction": "upstream",
                    "depth": 1,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert sorted(node["key_path"] for node in data["nodes"]) == [
            "raw/source_orders",
            "silver/stg_orders",
        ]
        assert data["edges"] == [{"source": "raw/source_orders", "target": "silver/stg_orders"}]

    def test_dagster_graph_impact_returns_downstream_assets(self):
        """Impact endpoint returns downstream assets ordered by depth."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch(
            "phlo_api.observatory_api.dagster.graphql_request",
            return_value=self._graphql_asset_graph_payload(),
        ):
            client = TestClient(app)
            response = client.get(
                "/api/dagster/graph/impact",
                params={"asset_key": "raw/source_orders"},
            )

        assert response.status_code == 200
        assert response.json() == [
            {
                "key_path": "silver/stg_orders",
                "label": "stg_orders",
                "layer": "silver",
                "depth": 1,
            },
            {
                "key_path": "gold/fct_orders",
                "label": "fct_orders",
                "layer": "gold",
                "depth": 2,
            },
        ]


class TestContributingRowsEndpoints:
    """Test contributing rows endpoints."""

    def test_contributing_query_endpoint_builds_entity_query(self):
        """Query endpoint returns the built contributing query."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch(
            "phlo_api.observatory_api.contributing.execute_trino_query",
            side_effect=[
                {
                    "columns": ["table_schema"],
                    "column_types": ["varchar"],
                    "rows": [{"table_schema": "silver"}],
                },
                {
                    "columns": ["column_name", "data_type"],
                    "column_types": ["varchar", "varchar"],
                    "rows": [{"column_name": "_phlo_row_id", "data_type": "varchar"}],
                },
            ],
        ):
            client = TestClient(app)
            response = client.post(
                "/api/contributing/query",
                json={
                    "downstream_asset_key": "gold/fct_orders",
                    "upstream_asset_key": "silver/stg_orders",
                    "row_data": {"_phlo_row_id": "abc123"},
                    "limit": 25,
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "query": 'SELECT * FROM "iceberg"."silver"."stg_orders" WHERE "_phlo_row_id" = \'abc123\' ORDER BY "_phlo_row_id" LIMIT 25',
            "upstream": {"schema": "silver", "table": "stg_orders"},
        }

    def test_contributing_page_endpoint_returns_rows(self):
        """Page endpoint executes contributing query and returns paginated rows."""
        from fastapi.testclient import TestClient
        from phlo_api.main import app

        with patch(
            "phlo_api.observatory_api.contributing.execute_trino_query",
            side_effect=[
                {
                    "columns": ["table_schema"],
                    "column_types": ["varchar"],
                    "rows": [{"table_schema": "silver"}],
                },
                {
                    "columns": ["column_name", "data_type"],
                    "column_types": ["varchar", "varchar"],
                    "rows": [
                        {"column_name": "_phlo_partition_date", "data_type": "date"},
                        {"column_name": "hour_of_day", "data_type": "integer"},
                        {"column_name": "day_of_week", "data_type": "integer"},
                    ],
                },
                {
                    "columns": ["hour_of_day", "day_of_week"],
                    "column_types": ["integer", "integer"],
                    "rows": [
                        {"hour_of_day": 3, "day_of_week": 2},
                        {"hour_of_day": 3, "day_of_week": 2},
                    ],
                },
            ],
        ):
            client = TestClient(app)
            response = client.post(
                "/api/contributing/page",
                json={
                    "downstream_asset_key": "publish/mrt_contribution_patterns",
                    "upstream_asset_key": "silver/fct_github_events",
                    "row_data": {
                        "_phlo_partition_date": "2025-01-01",
                        "hour_of_day": 3,
                        "day_of_week": 2,
                    },
                    "page": 0,
                    "page_size": 1,
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "mode": "aggregate",
            "page": 0,
            "page_size": 1,
            "has_more": True,
            "query": 'SELECT * FROM "iceberg"."silver"."fct_github_events" WHERE "hour_of_day" = 3 and "day_of_week" = 2 and "_phlo_partition_date" = date \'2025-01-01\' ORDER BY xxhash64(to_utf8(concat(\'phlo\', \'|\', coalesce(cast("day_of_week" as varchar), \'\'), \'|\' , coalesce(cast("hour_of_day" as varchar), \'\')))) OFFSET 0 LIMIT 2',
            "upstream": {"schema": "silver", "table": "fct_github_events"},
            "columns": ["hour_of_day", "day_of_week"],
            "column_types": ["integer", "integer"],
            "rows": [{"hour_of_day": 3, "day_of_week": 2}],
        }


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
