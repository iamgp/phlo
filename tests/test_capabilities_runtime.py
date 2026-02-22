from __future__ import annotations

import pytest

from phlo.capabilities import (
    CatalogSpec,
    QueryEngineSpec,
    TableStoreSpec,
    clear_capabilities,
    get_capability_registry,
    list_capabilities,
    missing_required_capabilities,
    register_catalog,
    register_query_engine,
    register_table_store,
    resolve_capability,
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

    registry = get_capability_registry()
    assert [spec.name for spec in registry.list_table_stores()] == ["iceberg"]
    assert [spec.name for spec in registry.list_catalogs()] == ["nessie"]
    assert [spec.name for spec in registry.list_query_engines()] == ["trino"]


def test_resolve_capability_prefers_explicit_name() -> None:
    register_query_engine(QueryEngineSpec(name="trino", provider={"engine": "trino"}))
    register_query_engine(QueryEngineSpec(name="duckdb", provider={"engine": "duckdb"}))

    resolved = resolve_capability("query_engine", "duckdb")
    assert resolved is not None
    assert resolved.name == "duckdb"
    assert resolved.provider == {"engine": "duckdb"}


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
