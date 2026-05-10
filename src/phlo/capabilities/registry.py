"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from phlo.capabilities.catalog import CapabilityFamily, named_family
from phlo.capabilities.specs import (
    AlertSinkSpec,
    ApiBackendSpec,
    AssetCheckSpec,
    AssetSpec,
    AuthenticationProviderSpec,
    AuthorizationPolicyBackendSpec,
    CatalogScannerSpec,
    CatalogSpec,
    DataMigrationSourceSpec,
    GovernanceBackendSpec,
    LineageSinkSpec,
    MaintenanceReadModelSpec,
    MetadataCatalogSpec,
    ObjectStoreSpec,
    ObservabilityBackendSpec,
    PublishTargetSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    RegulatedSurfaceSpec,
    ResourceSpec,
    SchemaMigrationSpec,
    SecretBackendSpec,
    TableStoreSpec,
    UiContributionSpec,
)


@dataclass
class CapabilityRegistry:
    """Thread-safe in-memory registry for capability specifications."""

    assets: dict[str, AssetSpec] = field(default_factory=dict)
    checks: dict[tuple[str, str], AssetCheckSpec] = field(default_factory=dict)
    resources: dict[str, ResourceSpec] = field(default_factory=dict)
    table_stores: dict[str, TableStoreSpec] = field(default_factory=dict)
    catalogs: dict[str, CatalogSpec] = field(default_factory=dict)
    catalog_scanners: dict[str, CatalogScannerSpec] = field(default_factory=dict)
    query_engines: dict[str, QueryEngineSpec] = field(default_factory=dict)
    object_stores: dict[str, ObjectStoreSpec] = field(default_factory=dict)
    quality_backends: dict[str, QualityBackendSpec] = field(default_factory=dict)
    maintenance_read_models: dict[str, MaintenanceReadModelSpec] = field(default_factory=dict)
    metadata_catalogs: dict[str, MetadataCatalogSpec] = field(default_factory=dict)
    lineage_sinks: dict[str, LineageSinkSpec] = field(default_factory=dict)
    governance_backends: dict[str, GovernanceBackendSpec] = field(default_factory=dict)
    authorization_policy_backends: dict[str, AuthorizationPolicyBackendSpec] = field(
        default_factory=dict
    )
    authentication_providers: dict[str, AuthenticationProviderSpec] = field(default_factory=dict)
    publish_targets: dict[str, PublishTargetSpec] = field(default_factory=dict)
    alert_sinks: dict[str, AlertSinkSpec] = field(default_factory=dict)
    api_backends: dict[str, ApiBackendSpec] = field(default_factory=dict)
    secret_backends: dict[str, SecretBackendSpec] = field(default_factory=dict)
    schema_migrators: dict[str, SchemaMigrationSpec] = field(default_factory=dict)
    data_migration_sources: dict[str, DataMigrationSourceSpec] = field(default_factory=dict)
    observability_backends: dict[str, ObservabilityBackendSpec] = field(default_factory=dict)
    regulated_surfaces: dict[str, RegulatedSurfaceSpec] = field(default_factory=dict)
    ui_contributions: dict[str, UiContributionSpec] = field(default_factory=dict)
    _asset_family: CapabilityFamily[AssetSpec, str] = field(
        default_factory=lambda: CapabilityFamily(key=lambda spec: spec.key),
        init=False,
        repr=False,
    )
    _check_family: CapabilityFamily[AssetCheckSpec, tuple[str, str]] = field(
        default_factory=lambda: CapabilityFamily(key=lambda spec: (spec.asset_key, spec.name)),
        init=False,
        repr=False,
    )
    _resource_family: CapabilityFamily[ResourceSpec, str] = field(
        default_factory=lambda: CapabilityFamily(key=lambda spec: spec.name),
        init=False,
        repr=False,
    )
    _table_store_family: CapabilityFamily[TableStoreSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _catalog_family: CapabilityFamily[CatalogSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _catalog_scanner_family: CapabilityFamily[CatalogScannerSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _query_engine_family: CapabilityFamily[QueryEngineSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _object_store_family: CapabilityFamily[ObjectStoreSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _quality_backend_family: CapabilityFamily[QualityBackendSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _maintenance_read_model_family: CapabilityFamily[MaintenanceReadModelSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _metadata_catalog_family: CapabilityFamily[MetadataCatalogSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _lineage_sink_family: CapabilityFamily[LineageSinkSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _governance_backend_family: CapabilityFamily[GovernanceBackendSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _authorization_policy_backend_family: CapabilityFamily[AuthorizationPolicyBackendSpec, str] = (
        field(
            default_factory=named_family,
            init=False,
            repr=False,
        )
    )
    _authentication_provider_family: CapabilityFamily[AuthenticationProviderSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _publish_target_family: CapabilityFamily[PublishTargetSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _alert_sink_family: CapabilityFamily[AlertSinkSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _api_backend_family: CapabilityFamily[ApiBackendSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _secret_backend_family: CapabilityFamily[SecretBackendSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _schema_migrator_family: CapabilityFamily[SchemaMigrationSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _data_migration_source_family: CapabilityFamily[DataMigrationSourceSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _observability_backend_family: CapabilityFamily[ObservabilityBackendSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _regulated_surface_family: CapabilityFamily[RegulatedSurfaceSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _ui_contribution_family: CapabilityFamily[UiContributionSpec, str] = field(
        default_factory=named_family,
        init=False,
        repr=False,
    )
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def register_asset(self, spec: AssetSpec) -> None:
        """Register or replace an asset spec by key.

        Args:
            spec: Asset capability specification to store.
        """

        with self._lock:
            self._asset_family.register(spec)
            self.assets = dict(self._asset_family._items)

    def register_check(self, spec: AssetCheckSpec) -> None:
        """Register or replace an asset check spec by asset/name tuple.

        Args:
            spec: Asset check capability specification to store.
        """

        with self._lock:
            self._check_family.register(spec)
            self.checks = dict(self._check_family._items)

    def register_resource(self, spec: ResourceSpec) -> None:
        """Register or replace a resource spec by name.

        Args:
            spec: Resource capability specification to store.
        """

        with self._lock:
            self._resource_family.register(spec)
            self.resources = dict(self._resource_family._items)

    def list_assets(self) -> list[AssetSpec]:
        """Return a snapshot list of all registered assets.

        Returns:
            List of currently registered asset specs.
        """

        with self._lock:
            return self._asset_family.list()

    def list_checks(self) -> list[AssetCheckSpec]:
        """Return a snapshot list of all registered checks.

        Returns:
            List of currently registered asset check specs.
        """

        with self._lock:
            return self._check_family.list()

    def list_resources(self) -> list[ResourceSpec]:
        """Return a snapshot list of all registered resources.

        Returns:
            List of currently registered resource specs.
        """

        with self._lock:
            return self._resource_family.list()

    def register_table_store(self, spec: TableStoreSpec) -> None:
        """Register or replace a table store spec by name."""
        with self._lock:
            self._table_store_family.register(spec)
            self.table_stores = dict(self._table_store_family._items)

    def list_table_stores(self) -> list[TableStoreSpec]:
        """Return a snapshot list of registered table store specs."""
        with self._lock:
            return self._table_store_family.list()

    def register_catalog(self, spec: CatalogSpec) -> None:
        """Register or replace a catalog spec by name."""
        with self._lock:
            self._catalog_family.register(spec)
            self.catalogs = dict(self._catalog_family._items)

    def list_catalogs(self) -> list[CatalogSpec]:
        """Return a snapshot list of registered catalog specs."""
        with self._lock:
            return self._catalog_family.list()

    def register_catalog_scanner(self, spec: CatalogScannerSpec) -> None:
        """Register or replace a catalog scanner spec by name."""
        with self._lock:
            self._catalog_scanner_family.register(spec)
            self.catalog_scanners = dict(self._catalog_scanner_family._items)

    def list_catalog_scanners(self) -> list[CatalogScannerSpec]:
        """Return a snapshot list of registered catalog scanner specs."""
        with self._lock:
            return self._catalog_scanner_family.list()

    def register_query_engine(self, spec: QueryEngineSpec) -> None:
        """Register or replace a query engine spec by name."""
        with self._lock:
            self._query_engine_family.register(spec)
            self.query_engines = dict(self._query_engine_family._items)

    def list_query_engines(self) -> list[QueryEngineSpec]:
        """Return a snapshot list of registered query engine specs."""
        with self._lock:
            return self._query_engine_family.list()

    def register_object_store(self, spec: ObjectStoreSpec) -> None:
        """Register or replace an object store spec by name."""
        with self._lock:
            self._object_store_family.register(spec)
            self.object_stores = dict(self._object_store_family._items)

    def list_object_stores(self) -> list[ObjectStoreSpec]:
        """Return a snapshot list of registered object store specs."""
        with self._lock:
            return self._object_store_family.list()

    def register_quality_backend(self, spec: QualityBackendSpec) -> None:
        """Register or replace a quality backend spec by name."""
        with self._lock:
            self._quality_backend_family.register(spec)
            self.quality_backends = dict(self._quality_backend_family._items)

    def list_quality_backends(self) -> list[QualityBackendSpec]:
        """Return a snapshot list of registered quality backend specs."""
        with self._lock:
            return self._quality_backend_family.list()

    def register_maintenance_read_model(self, spec: MaintenanceReadModelSpec) -> None:
        """Register or replace a maintenance read-model spec by name."""
        with self._lock:
            self._maintenance_read_model_family.register(spec)
            self.maintenance_read_models = dict(self._maintenance_read_model_family._items)

    def list_maintenance_read_models(self) -> list[MaintenanceReadModelSpec]:
        """Return a snapshot list of maintenance read-model specs."""
        with self._lock:
            return self._maintenance_read_model_family.list()

    def register_metadata_catalog(self, spec: MetadataCatalogSpec) -> None:
        """Register or replace a metadata catalog spec by name."""
        with self._lock:
            self._metadata_catalog_family.register(spec)
            self.metadata_catalogs = dict(self._metadata_catalog_family._items)

    def list_metadata_catalogs(self) -> list[MetadataCatalogSpec]:
        """Return a snapshot list of registered metadata catalog specs."""
        with self._lock:
            return self._metadata_catalog_family.list()

    def register_lineage_sink(self, spec: LineageSinkSpec) -> None:
        """Register or replace a lineage sink spec by name."""
        with self._lock:
            self._lineage_sink_family.register(spec)
            self.lineage_sinks = dict(self._lineage_sink_family._items)

    def list_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Return a snapshot list of registered lineage sink specs."""
        with self._lock:
            return self._lineage_sink_family.list()

    def register_governance_backend(self, spec: GovernanceBackendSpec) -> None:
        """Register or replace a governance backend spec by name."""
        with self._lock:
            self._governance_backend_family.register(spec)
            self.governance_backends = dict(self._governance_backend_family._items)

    def list_governance_backends(self) -> list[GovernanceBackendSpec]:
        """Return a snapshot list of registered governance backend specs."""
        with self._lock:
            return self._governance_backend_family.list()

    def register_authorization_policy_backend(self, spec: AuthorizationPolicyBackendSpec) -> None:
        """Register or replace an authorization policy backend spec by name."""
        with self._lock:
            self._authorization_policy_backend_family.register(spec)
            self.authorization_policy_backends = dict(
                self._authorization_policy_backend_family._items
            )

    def list_authorization_policy_backends(self) -> list[AuthorizationPolicyBackendSpec]:
        """Return a snapshot list of registered authorization policy backend specs."""
        with self._lock:
            return self._authorization_policy_backend_family.list()

    def register_authentication_provider(self, spec: AuthenticationProviderSpec) -> None:
        """Register or replace an authentication provider spec by name."""
        with self._lock:
            self._authentication_provider_family.register(spec)
            self.authentication_providers = dict(self._authentication_provider_family._items)

    def list_authentication_providers(self) -> list[AuthenticationProviderSpec]:
        """Return a snapshot list of registered authentication provider specs."""
        with self._lock:
            return self._authentication_provider_family.list()

    def register_publish_target(self, spec: PublishTargetSpec) -> None:
        """Register or replace a publish target spec by name."""
        with self._lock:
            self._publish_target_family.register(spec)
            self.publish_targets = dict(self._publish_target_family._items)

    def list_publish_targets(self) -> list[PublishTargetSpec]:
        """Return a snapshot list of registered publish target specs."""
        with self._lock:
            return self._publish_target_family.list()

    def register_alert_sink(self, spec: AlertSinkSpec) -> None:
        """Register or replace an alert sink spec by name."""
        with self._lock:
            self._alert_sink_family.register(spec)
            self.alert_sinks = dict(self._alert_sink_family._items)

    def list_alert_sinks(self) -> list[AlertSinkSpec]:
        """Return a snapshot list of registered alert sink specs."""
        with self._lock:
            return self._alert_sink_family.list()

    def register_api_backend(self, spec: ApiBackendSpec) -> None:
        """Register or replace an API backend spec by name."""
        with self._lock:
            self._api_backend_family.register(spec)
            self.api_backends = dict(self._api_backend_family._items)

    def list_api_backends(self) -> list[ApiBackendSpec]:
        """Return a snapshot list of registered API backend specs."""
        with self._lock:
            return self._api_backend_family.list()

    def register_secret_backend(self, spec: SecretBackendSpec) -> None:
        """Register or replace a secret backend spec by name."""
        with self._lock:
            self._secret_backend_family.register(spec)
            self.secret_backends = dict(self._secret_backend_family._items)

    def list_secret_backends(self) -> list[SecretBackendSpec]:
        """Return a snapshot list of registered secret backend specs."""
        with self._lock:
            return self._secret_backend_family.list()

    def register_schema_migrator(self, spec: SchemaMigrationSpec) -> None:
        """Register or replace a schema migrator spec by name."""
        with self._lock:
            self._schema_migrator_family.register(spec)
            self.schema_migrators = dict(self._schema_migrator_family._items)

    def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Return a snapshot list of registered schema migrator specs."""
        with self._lock:
            return self._schema_migrator_family.list()

    def register_data_migration_source(self, spec: DataMigrationSourceSpec) -> None:
        """Register or replace a data migration source adapter spec by name."""
        with self._lock:
            self._data_migration_source_family.register(spec)
            self.data_migration_sources = dict(self._data_migration_source_family._items)

    def list_data_migration_sources(self) -> list[DataMigrationSourceSpec]:
        """Return a snapshot list of registered migration source adapter specs."""
        with self._lock:
            return self._data_migration_source_family.list()

    def register_observability_backend(self, spec: ObservabilityBackendSpec) -> None:
        """Register or replace an observability backend spec by name."""
        with self._lock:
            self._observability_backend_family.register(spec)
            self.observability_backends = dict(self._observability_backend_family._items)

    def list_observability_backends(self) -> list[ObservabilityBackendSpec]:
        """Return a snapshot list of registered observability backend specs."""
        with self._lock:
            return self._observability_backend_family.list()

    def register_regulated_surface(self, spec: RegulatedSurfaceSpec) -> None:
        """Register or replace a regulated surface spec by name."""
        with self._lock:
            self._regulated_surface_family.register(spec)
            self.regulated_surfaces = dict(self._regulated_surface_family._items)

    def list_regulated_surfaces(self) -> list[RegulatedSurfaceSpec]:
        """Return a snapshot list of registered regulated surface specs."""
        with self._lock:
            return self._regulated_surface_family.list()

    def register_ui_contribution(self, spec: UiContributionSpec) -> None:
        """Register or replace a UI contribution spec by name."""
        with self._lock:
            self._ui_contribution_family.register(spec)
            self.ui_contributions = dict(self._ui_contribution_family._items)

    def list_ui_contributions(self) -> list[UiContributionSpec]:
        """Return a snapshot list of registered UI contribution specs."""
        with self._lock:
            return self._ui_contribution_family.list()

    def clear(self) -> None:
        """Remove all assets, checks, and resources from the registry."""

        with self._lock:
            self._asset_family.clear()
            self.assets = dict(self._asset_family._items)
            self._check_family.clear()
            self.checks = dict(self._check_family._items)
            self._resource_family.clear()
            self.resources = dict(self._resource_family._items)
            self._table_store_family.clear()
            self.table_stores = dict(self._table_store_family._items)
            self._catalog_family.clear()
            self.catalogs = dict(self._catalog_family._items)
            self._catalog_scanner_family.clear()
            self.catalog_scanners = dict(self._catalog_scanner_family._items)
            self._query_engine_family.clear()
            self.query_engines = dict(self._query_engine_family._items)
            self._object_store_family.clear()
            self.object_stores = dict(self._object_store_family._items)
            self._quality_backend_family.clear()
            self.quality_backends = dict(self._quality_backend_family._items)
            self._maintenance_read_model_family.clear()
            self.maintenance_read_models = dict(self._maintenance_read_model_family._items)
            self._metadata_catalog_family.clear()
            self.metadata_catalogs = dict(self._metadata_catalog_family._items)
            self._lineage_sink_family.clear()
            self.lineage_sinks = dict(self._lineage_sink_family._items)
            self._governance_backend_family.clear()
            self.governance_backends = dict(self._governance_backend_family._items)
            self._authorization_policy_backend_family.clear()
            self.authorization_policy_backends = dict(
                self._authorization_policy_backend_family._items
            )
            self._authentication_provider_family.clear()
            self.authentication_providers = dict(self._authentication_provider_family._items)
            self._publish_target_family.clear()
            self.publish_targets = dict(self._publish_target_family._items)
            self._alert_sink_family.clear()
            self.alert_sinks = dict(self._alert_sink_family._items)
            self._api_backend_family.clear()
            self.api_backends = dict(self._api_backend_family._items)
            self._secret_backend_family.clear()
            self.secret_backends = dict(self._secret_backend_family._items)
            self._schema_migrator_family.clear()
            self.schema_migrators = dict(self._schema_migrator_family._items)
            self._data_migration_source_family.clear()
            self.data_migration_sources = dict(self._data_migration_source_family._items)
            self._observability_backend_family.clear()
            self.observability_backends = dict(self._observability_backend_family._items)
            self._regulated_surface_family.clear()
            self.regulated_surfaces = dict(self._regulated_surface_family._items)
            self._ui_contribution_family.clear()
            self.ui_contributions = dict(self._ui_contribution_family._items)

    def clear_checks(self) -> None:
        """Remove all registered checks while preserving assets/resources."""

        with self._lock:
            self._check_family.clear()
            self.checks = dict(self._check_family._items)


_GLOBAL_REGISTRY = CapabilityRegistry()


def get_capability_registry() -> CapabilityRegistry:
    """Return the process-global capability registry instance.

    Returns:
        Shared in-memory capability registry.
    """

    return _GLOBAL_REGISTRY


def register_asset(spec: AssetSpec) -> None:
    """Register an asset in the process-global registry.

    Args:
        spec: Asset capability specification to store.
    """

    _GLOBAL_REGISTRY.register_asset(spec)


def register_check(spec: AssetCheckSpec) -> None:
    """Register an asset check in the process-global registry.

    Args:
        spec: Asset check capability specification to store.
    """

    _GLOBAL_REGISTRY.register_check(spec)


def register_resource(spec: ResourceSpec) -> None:
    """Register a resource in the process-global registry.

    Args:
        spec: Resource capability specification to store.
    """

    _GLOBAL_REGISTRY.register_resource(spec)


def register_table_store(spec: TableStoreSpec) -> None:
    """Register a table store in the process-global registry."""
    _GLOBAL_REGISTRY.register_table_store(spec)


def register_catalog(spec: CatalogSpec) -> None:
    """Register a catalog in the process-global registry."""
    _GLOBAL_REGISTRY.register_catalog(spec)


def register_catalog_scanner(spec: CatalogScannerSpec) -> None:
    """Register a catalog scanner in the process-global registry."""
    _GLOBAL_REGISTRY.register_catalog_scanner(spec)


def register_query_engine(spec: QueryEngineSpec) -> None:
    """Register a query engine in the process-global registry."""
    _GLOBAL_REGISTRY.register_query_engine(spec)


def register_object_store(spec: ObjectStoreSpec) -> None:
    """Register an object store in the process-global registry."""
    _GLOBAL_REGISTRY.register_object_store(spec)


def register_quality_backend(spec: QualityBackendSpec) -> None:
    """Register a quality backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_quality_backend(spec)


def register_maintenance_read_model(spec: MaintenanceReadModelSpec) -> None:
    """Register a maintenance read model in the process-global registry."""
    _GLOBAL_REGISTRY.register_maintenance_read_model(spec)


def register_metadata_catalog(spec: MetadataCatalogSpec) -> None:
    """Register a metadata catalog in the process-global registry."""
    _GLOBAL_REGISTRY.register_metadata_catalog(spec)


def register_lineage_sink(spec: LineageSinkSpec) -> None:
    """Register a lineage sink in the process-global registry."""
    _GLOBAL_REGISTRY.register_lineage_sink(spec)


def register_governance_backend(spec: GovernanceBackendSpec) -> None:
    """Register a governance backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_governance_backend(spec)


def register_authorization_policy_backend(spec: AuthorizationPolicyBackendSpec) -> None:
    """Register an authorization policy backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_authorization_policy_backend(spec)


def register_authentication_provider(spec: AuthenticationProviderSpec) -> None:
    """Register an authentication provider in the process-global registry."""
    _GLOBAL_REGISTRY.register_authentication_provider(spec)


def register_publish_target(spec: PublishTargetSpec) -> None:
    """Register a publish target in the process-global registry."""
    _GLOBAL_REGISTRY.register_publish_target(spec)


def register_alert_sink(spec: AlertSinkSpec) -> None:
    """Register an alert sink in the process-global registry."""
    _GLOBAL_REGISTRY.register_alert_sink(spec)


def register_api_backend(spec: ApiBackendSpec) -> None:
    """Register an API backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_api_backend(spec)


def register_secret_backend(spec: SecretBackendSpec) -> None:
    """Register a secret backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_secret_backend(spec)


def register_schema_migrator(spec: SchemaMigrationSpec) -> None:
    """Register a schema migrator in the process-global registry."""
    _GLOBAL_REGISTRY.register_schema_migrator(spec)


def register_data_migration_source(spec: DataMigrationSourceSpec) -> None:
    """Register a data migration source adapter in the global registry."""
    _GLOBAL_REGISTRY.register_data_migration_source(spec)


def register_observability_backend(spec: ObservabilityBackendSpec) -> None:
    """Register an observability backend in the global registry."""
    _GLOBAL_REGISTRY.register_observability_backend(spec)


def register_regulated_surface(spec: RegulatedSurfaceSpec) -> None:
    """Register a regulated surface in the global registry."""
    _GLOBAL_REGISTRY.register_regulated_surface(spec)


def list_regulated_surfaces() -> list[RegulatedSurfaceSpec]:
    """Return a snapshot list of registered regulated surface specs."""
    return _GLOBAL_REGISTRY.list_regulated_surfaces()


def clear_capabilities() -> None:
    """Clear all capability types from the global registry."""

    _GLOBAL_REGISTRY.clear()
