from types import SimpleNamespace

from phlo_api.observatory_api.v2_capabilities import build_capability_inventory
from phlo_api.observatory_api.v2 import _pages_from_inventory
from phlo_api.observatory_api.v2_models import (
    V2CapabilityInventory,
    V2CapabilityProvider,
    V2CapabilitySupport,
    V2RouteRequirement,
)


class FakeRegistry:
    def list_query_engines(self):
        return [
            SimpleNamespace(
                name="trino",
                metadata={
                    "service_type": "Trino",
                    "url": "http://secret-host",
                    "endpoint": "http://secret-endpoint",
                    "dsn": "postgres://secret",
                    "connection_string": "postgres://secret",
                    "harmless_name": "http://internal",
                    "nested": {
                        "safe": "ok",
                        "secret": "hidden",
                        "nested_url": "http://internal",
                    },
                    "items": [
                        {"name": "safe-item", "endpoint": "http://nested-endpoint"},
                        {"connection": "hidden", "enabled": True},
                        {"name": "unsafe-value", "location": "http://internal"},
                    ],
                    "native_links": [
                        {
                            "label": "Open",
                            "url": "http://internal.example/ui?token=secret",
                            "kind": "app",
                        }
                    ],
                },
                support={"supports_metrics": True},
            )
        ]

    def list_table_stores(self):
        return []

    def list_catalogs(self):
        return []

    def list_catalog_scanners(self):
        return []

    def list_object_stores(self):
        return []

    def list_quality_backends(self):
        return []

    def list_maintenance_read_models(self):
        return []

    def list_metadata_catalogs(self):
        return []

    def list_lineage_sinks(self):
        return []

    def list_governance_backends(self):
        return []

    def list_authorization_policy_backends(self):
        return []

    def list_authentication_providers(self):
        return []

    def list_publish_targets(self):
        return []

    def list_alert_sinks(self):
        return []

    def list_api_backends(self):
        return []

    def list_observability_backends(self):
        return []

    def list_regulated_surfaces(self):
        return []


def test_v2_capability_inventory_serializes_support_and_requirements() -> None:
    provider = V2CapabilityProvider(
        capability_type="query_engine",
        name="trino",
        display_name="Trino",
        package="phlo-trino",
        metadata={"service_type": "Trino"},
        support=V2CapabilitySupport(
            supports_metrics=True,
            supports_permissions=True,
        ),
        health={"state": "ok", "message": "registered"},
        native_links=[{"label": "Open", "url": "http://localhost:8080/ui", "kind": "app"}],
    )
    inventory = V2CapabilityInventory(
        version=2,
        providers={"query_engine": [provider]},
        requirements=[
            V2RouteRequirement(
                route_id="data",
                label="Data",
                path="/v2/data",
                required_any=["query_engine", "table_store"],
            )
        ],
    )

    payload = inventory.model_dump()

    assert payload["providers"]["query_engine"][0]["name"] == "trino"
    assert payload["providers"]["query_engine"][0]["support"]["supports_metrics"] is True
    assert payload["requirements"][0]["required_any"] == ["query_engine", "table_store"]


def test_build_capability_inventory_serializes_registry_without_private_urls() -> None:
    inventory = build_capability_inventory(FakeRegistry())
    metadata = inventory.providers["query_engine"][0].metadata

    assert inventory.providers["query_engine"][0].name == "trino"
    assert inventory.providers["query_engine"][0].support.supports_metrics is True
    assert "url" not in metadata
    assert "endpoint" not in metadata
    assert "dsn" not in metadata
    assert "connection_string" not in metadata
    assert "harmless_name" not in metadata
    assert inventory.providers["query_engine"][0].native_links == []
    assert metadata["nested"] == {"safe": "ok"}
    assert metadata["items"] == [{"name": "safe-item"}, {"enabled": True}, {"name": "unsafe-value"}]


def test_inventory_includes_ui_contributions() -> None:
    registry = SimpleNamespace(
        list_query_engines=lambda: [],
        list_ui_contributions=lambda: [
            SimpleNamespace(
                name="trino-data",
                capability_type="query_engine",
                capability_name="trino",
                surfaces=["data"],
                read_models={"tables": "/api/observatory/v2/tables"},
                actions=["query.run"],
                native_links=[],
                metadata={"safe": "yes", "url": "http://internal"},
            )
        ],
    )

    inventory = build_capability_inventory(registry)

    assert inventory.ui_contributions[0].name == "trino-data"
    assert inventory.ui_contributions[0].surfaces == ["data"]
    assert "url" not in inventory.ui_contributions[0].metadata


def test_build_capability_inventory_route_requirements_use_emitted_provider_keys() -> None:
    inventory = build_capability_inventory(FakeRegistry())
    requirements = {requirement.route_id: requirement for requirement in inventory.requirements}

    assert list(requirements) == [
        "overview",
        "data",
        "workflows",
        "assets",
        "issues",
        "quality",
        "logs",
        "branches",
        "operations",
        "runs",
        "storage",
        "observability",
        "governance",
        "catalog",
        "apis",
        "bi",
        "extensions",
        "services",
        "settings",
    ]
    assert requirements["data"].required_any == ["query_engine", "table_store"]
    assert requirements["data"].optional == []
    assert requirements["assets"].required_any == [
        "query_engine",
        "table_store",
        "lineage_sink",
    ]
    assert requirements["assets"].optional == [
        "quality_backend",
        "maintenance_read_model",
    ]
    assert requirements["issues"].required_any == ["quality_backend"]
    assert requirements["issues"].nav is True
    assert requirements["quality"].required_any == ["quality_backend"]
    assert requirements["quality"].nav is False
    assert requirements["logs"].required_any == ["observability_backend"]
    assert requirements["logs"].optional == ["maintenance_read_model"]
    assert requirements["branches"].required_any == ["catalog"]
    assert requirements["branches"].optional == ["table_store"]
    assert requirements["operations"].required_any == ["maintenance_read_model"]
    assert requirements["runs"].required_any == []
    assert requirements["runs"].optional == ["maintenance_read_model"]
    assert requirements["storage"].required_any == ["table_store", "object_store"]
    assert requirements["storage"].optional == []
    assert requirements["observability"].required_any == ["observability_backend"]
    assert requirements["observability"].optional == ["alert_sink"]
    assert requirements["governance"].required_any == [
        "governance_backend",
        "authorization_policy_backend",
        "authentication_provider",
        "regulated_surface",
    ]
    assert requirements["governance"].optional == []
    assert requirements["catalog"].required_any == [
        "metadata_catalog",
        "catalog_scanner",
    ]
    assert requirements["catalog"].optional == []
    assert requirements["apis"].required_any == ["api_backend"]
    assert requirements["apis"].optional == []
    assert requirements["bi"].required_any == ["publish_target"]
    assert requirements["bi"].optional == ["query_engine"]
    assert requirements["extensions"].required_any == ["observatory_extension"]
    assert requirements["extensions"].nav is False
    assert requirements["overview"].required_any == []
    assert requirements["services"].required_any == []
    assert requirements["settings"].required_any == []
    assert "asset_provider" not in set().union(
        *(
            set(requirement.required_any) | set(requirement.optional)
            for requirement in requirements.values()
        )
    )
    assert "orchestrator" not in set().union(
        *(
            set(requirement.required_any) | set(requirement.optional)
            for requirement in requirements.values()
        )
    )


def test_pages_from_inventory_enables_routes_by_required_capabilities() -> None:
    inventory = V2CapabilityInventory(
        providers={
            "query_engine": [
                V2CapabilityProvider(
                    capability_type="query_engine",
                    name="trino",
                    display_name="Trino",
                )
            ]
        },
        requirements=[
            V2RouteRequirement(
                route_id="data",
                label="Data",
                path="/v2/data",
                required_any=["query_engine", "table_store"],
                reason="Install data provider.",
            ),
            V2RouteRequirement(
                route_id="storage",
                label="Storage",
                path="/v2/storage",
                required_any=["object_store"],
                reason="Install storage provider.",
            ),
        ],
    )

    pages = _pages_from_inventory(inventory)

    assert {page.id: page.available for page in pages} == {
        "data": True,
        "storage": False,
    }
    assert pages[0].providers == ["trino"]
