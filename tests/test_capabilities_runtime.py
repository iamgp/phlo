from __future__ import annotations

import pytest

from phlo.capabilities import (
    CapabilitySupport,
    CatalogSpec,
    QueryEngineSpec,
    RuntimeRouting,
    SchemaMigrationSpec,
    TableStoreSpec,
    clear_capabilities,
    get_capability_registry,
    list_capabilities,
    missing_required_capabilities,
    register_catalog,
    register_query_engine,
    register_schema_migrator,
    register_table_store,
    resolve_capability,
    routing_from_context,
)
from phlo.plugins.base import PluginMetadata

pytestmark = pytest.mark.core_regression


def teardown_function() -> None:
    """Reset global capability registry between tests."""
    clear_capabilities()


def test_registry_tracks_new_platform_capability_types() -> None:
    register_table_store(TableStoreSpec(name="iceberg", provider=object()))
    register_catalog(CatalogSpec(name="nessie", provider=object()))
    register_query_engine(QueryEngineSpec(name="trino", provider=object()))
    register_schema_migrator(SchemaMigrationSpec(name="iceberg", provider=object()))

    registry = get_capability_registry()
    assert [spec.name for spec in registry.list_table_stores()] == ["iceberg"]
    assert [spec.name for spec in registry.list_catalogs()] == ["nessie"]
    assert [spec.name for spec in registry.list_query_engines()] == ["trino"]
    assert [spec.name for spec in registry.list_schema_migrators()] == ["iceberg"]


def test_resolve_capability_prefers_explicit_name() -> None:
    register_query_engine(
        QueryEngineSpec(
            name="trino",
            provider={"engine": "trino"},
            support=CapabilitySupport(supports_refs=True),
        )
    )
    register_query_engine(QueryEngineSpec(name="duckdb", provider={"engine": "duckdb"}))

    resolved = resolve_capability("query_engine", "duckdb")
    assert resolved is not None
    assert resolved.name == "duckdb"
    assert resolved.provider == {"engine": "duckdb"}
    assert resolved.support.supports_refs is False


def test_resolve_capability_returns_support_metadata() -> None:
    register_table_store(
        TableStoreSpec(
            name="iceberg",
            provider=object(),
            support=CapabilitySupport(
                supports_refs=True,
                supports_schema_evolution=True,
                supports_time_travel=True,
            ),
        )
    )

    resolved = resolve_capability("table_store", "iceberg")
    assert resolved is not None
    assert resolved.support.supports_refs is True
    assert resolved.support.supports_schema_evolution is True
    assert resolved.support.supports_time_travel is True


def test_missing_required_capabilities_reports_unsatisfied_requirements() -> None:
    register_catalog(CatalogSpec(name="nessie", provider=object()))

    plugin = PluginMetadata(
        name="test_plugin",
        version="0.0.1",
        requires_capabilities=["catalog:nessie", "query_engine:trino", "table_store"],
    )
    missing = missing_required_capabilities(plugin)
    assert missing == ["query_engine:trino", "table_store"]


def test_list_capabilities_returns_registered_names() -> None:
    register_table_store(TableStoreSpec(name="iceberg", provider=object()))
    register_table_store(TableStoreSpec(name="delta", provider=object()))

    assert sorted(list_capabilities("table_store")) == ["delta", "iceberg"]


def test_list_capabilities_returns_schema_migrators() -> None:
    register_schema_migrator(SchemaMigrationSpec(name="iceberg", provider=object()))

    assert list_capabilities("schema_migrator") == ["iceberg"]


def test_plugin_metadata_support_defaults_to_empty() -> None:
    metadata = PluginMetadata(name="test-plugin", version="1.0.0")

    assert metadata.support == CapabilitySupport()


def test_routing_from_context_reads_canonical_tags() -> None:
    class StubRuntime:
        run_id = "run-123"
        partition_key = "2025-01-01"
        tags = {
            "environment": "dev",
            "branch": "feature/orders",
            "feature/wap": "true",
        }
        resources = {"table_store": object()}

        @property
        def logger(self) -> object:
            return object()

        @property
        def routing(self) -> RuntimeRouting:
            raise AttributeError

        def get_resource(self, name: str) -> object:
            return self.resources[name]

    routing = routing_from_context(StubRuntime())
    assert routing.environment == "dev"
    assert routing.ref == "feature/orders"
    assert routing.partition_key == "2025-01-01"
    assert routing.run_id == "run-123"
    assert routing.feature_flags == {"wap": "true"}
    assert "table_store" in routing.resources
