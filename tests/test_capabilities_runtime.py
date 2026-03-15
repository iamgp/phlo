from __future__ import annotations

import pytest

from phlo.capabilities import (
    ApiBackendSpec,
    CapabilitySupport,
    CatalogSpec,
    LineageSinkSpec,
    MetadataCatalogSpec,
    ObservabilityBackendSpec,
    PublishTargetSpec,
    QueryEngineSpec,
    RuntimeRouting,
    SchemaMigrationSpec,
    TableStoreSpec,
    clear_capabilities,
    get_capability_registry,
    list_capabilities,
    missing_required_capabilities,
    register_catalog,
    register_lineage_sink,
    register_metadata_catalog,
    register_observability_backend,
    register_publish_target,
    register_query_engine,
    register_schema_migrator,
    register_table_store,
    resolve_capability,
    resolve_runtime_ref,
    routing_from_context,
)
from phlo.config import _get_config
from phlo.plugins.base import PluginMetadata

pytestmark = pytest.mark.core_regression


def teardown_function() -> None:
    """Reset global capability registry between tests."""
    _get_config.cache_clear()
    from phlo.infrastructure import clear_config_cache

    clear_config_cache()
    clear_capabilities()


def test_registry_tracks_new_platform_capability_types() -> None:
    register_table_store(TableStoreSpec(name="iceberg", provider=object()))
    register_catalog(CatalogSpec(name="nessie", provider=object()))
    register_query_engine(QueryEngineSpec(name="trino", provider=object()))
    register_schema_migrator(SchemaMigrationSpec(name="iceberg", provider=object()))
    register_publish_target(PublishTargetSpec(name="postgres", provider=object()))

    registry = get_capability_registry()

    def names(specs):
        return {spec.name for spec in specs}

    assert "iceberg" in names(registry.list_table_stores())
    assert "nessie" in names(registry.list_catalogs())
    assert "trino" in names(registry.list_query_engines())
    assert "iceberg" in names(registry.list_schema_migrators())
    assert "postgres" in names(registry.list_publish_targets())


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


def test_list_capabilities_returns_publish_targets() -> None:
    register_publish_target(PublishTargetSpec(name="postgres", provider=object()))

    assert list_capabilities("publish_target") == ["postgres"]


def test_registry_tracks_api_backends() -> None:
    from phlo.capabilities import register_api_backend

    register_api_backend(ApiBackendSpec(name="hasura", provider=object()))

    registry = get_capability_registry()
    assert [spec.name for spec in registry.list_api_backends()] == ["hasura"]


def test_resolve_metadata_and_lineage_capabilities() -> None:
    register_metadata_catalog(MetadataCatalogSpec(name="openmetadata", provider={"catalog": True}))
    register_lineage_sink(LineageSinkSpec(name="phlo-lineage", provider={"lineage": True}))

    metadata = resolve_capability("metadata_catalog", "openmetadata")
    lineage = resolve_capability("lineage_sink", "phlo-lineage")

    assert metadata is not None
    assert metadata.provider == {"catalog": True}
    assert lineage is not None
    assert lineage.provider == {"lineage": True}


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
            "phlo/capability/table_store": "delta",
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
    assert routing.capability_overrides == {"table_store": "delta"}
    assert "table_store" in routing.resources


def test_resolve_capability_uses_global_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHLO_DEFAULT_CAPABILITIES", '{"table_store":"delta"}')
    _get_config.cache_clear()
    register_table_store(TableStoreSpec(name="iceberg", provider={"engine": "iceberg"}))
    register_table_store(TableStoreSpec(name="delta", provider={"engine": "delta"}))

    resolved = resolve_capability("table_store")

    assert resolved is not None
    assert resolved.name == "delta"
    assert resolved.provider == {"engine": "delta"}


def test_resolve_capability_uses_phlo_yaml_default(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    table_store: iceberg\n",
        encoding="utf-8",
    )
    register_table_store(TableStoreSpec(name="iceberg", provider={"engine": "iceberg"}))
    register_table_store(TableStoreSpec(name="delta", provider={"engine": "delta"}))

    resolved = resolve_capability("table_store")

    assert resolved is not None
    assert resolved.name == "iceberg"


def test_env_default_overrides_phlo_yaml_default(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    table_store: iceberg\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PHLO_DEFAULT_CAPABILITIES", '{"table_store":"delta"}')
    _get_config.cache_clear()
    register_table_store(TableStoreSpec(name="iceberg", provider={"engine": "iceberg"}))
    register_table_store(TableStoreSpec(name="delta", provider={"engine": "delta"}))

    resolved = resolve_capability("table_store")

    assert resolved is not None
    assert resolved.name == "delta"


def test_resolve_capability_uses_runtime_override_over_global_default() -> None:
    register_table_store(TableStoreSpec(name="iceberg", provider={"engine": "iceberg"}))
    register_table_store(TableStoreSpec(name="delta", provider={"engine": "delta"}))

    runtime = type(
        "StubRuntime",
        (),
        {
            "run_id": "run-123",
            "partition_key": None,
            "tags": {"phlo/capability/table_store": "iceberg"},
            "resources": {},
            "logger": property(lambda self: object()),
            "routing": property(lambda self: (_ for _ in ()).throw(AttributeError())),
            "get_resource": lambda self, name: None,
        },
    )()

    resolved = resolve_capability("table_store", runtime=runtime)

    assert resolved is not None
    assert resolved.name == "iceberg"


def test_resolve_runtime_ref_returns_routing_ref_when_supported() -> None:
    runtime = type(
        "StubRuntime",
        (),
        {
            "run_id": "run-123",
            "partition_key": None,
            "tags": {"phlo/ref": "feature/orders"},
            "resources": {},
            "logger": property(lambda self: object()),
            "routing": property(lambda self: (_ for _ in ()).throw(AttributeError())),
            "get_resource": lambda self, name: None,
        },
    )()

    assert (
        resolve_runtime_ref(
            runtime,
            support=CapabilitySupport(supports_refs=True),
            default_ref="main",
        )
        == "feature/orders"
    )


def test_resolve_runtime_ref_uses_default_for_ref_aware_capability() -> None:
    runtime = type(
        "StubRuntime",
        (),
        {
            "run_id": "run-123",
            "partition_key": None,
            "tags": {},
            "resources": {},
            "logger": property(lambda self: object()),
            "routing": property(lambda self: (_ for _ in ()).throw(AttributeError())),
            "get_resource": lambda self, name: None,
        },
    )()

    assert (
        resolve_runtime_ref(
            runtime,
            support=CapabilitySupport(supports_refs=True),
            default_ref="main",
        )
        == "main"
    )


def test_resolve_runtime_ref_ignores_ref_for_non_versioned_capability() -> None:
    runtime = type(
        "StubRuntime",
        (),
        {
            "run_id": "run-123",
            "partition_key": None,
            "tags": {"phlo/ref": "feature/orders"},
            "resources": {},
            "logger": property(lambda self: object()),
            "routing": property(lambda self: (_ for _ in ()).throw(AttributeError())),
            "get_resource": lambda self, name: None,
        },
    )()

    assert (
        resolve_runtime_ref(
            runtime,
            support=CapabilitySupport(supports_refs=False),
            default_ref="main",
        )
        is None
    )


def test_registry_tracks_observability_backend_capability() -> None:
    """Observability backend capability should be registrable and listable."""
    mock_backend = object()
    register_observability_backend(ObservabilityBackendSpec(name="default", provider=mock_backend))

    registry = get_capability_registry()
    specs = registry.list_observability_backends()

    assert len(specs) == 1
    assert specs[0].name == "default"
    assert specs[0].provider is mock_backend


def test_resolve_observability_backend_capability() -> None:
    """Should be able to resolve observability backend capability by name."""
    mock_backend = object()
    register_observability_backend(ObservabilityBackendSpec(name="default", provider=mock_backend))

    resolved = resolve_capability("observability_backend", "default")

    assert resolved is not None
    assert resolved.name == "default"
    assert resolved.provider is mock_backend


def test_list_observability_backend_capabilities() -> None:
    """list_capabilities should return observability backend names."""
    mock_backend = object()
    register_observability_backend(ObservabilityBackendSpec(name="default", provider=mock_backend))
    register_observability_backend(ObservabilityBackendSpec(name="custom", provider=object()))

    names = list_capabilities("observability_backend")

    assert "default" in names
    assert "custom" in names


def test_observability_support_flags_round_trip() -> None:
    """Observability support flags should survive resolution."""
    register_observability_backend(
        ObservabilityBackendSpec(
            name="default",
            provider=object(),
            support=CapabilitySupport(
                supports_metrics=True,
                supports_logs=True,
                supports_dashboards=True,
                supports_alerts=True,
            ),
        )
    )

    resolved = resolve_capability("observability_backend", "default")

    assert resolved is not None
    assert resolved.support.supports_metrics is True
    assert resolved.support.supports_logs is True
    assert resolved.support.supports_dashboards is True
    assert resolved.support.supports_alerts is True
