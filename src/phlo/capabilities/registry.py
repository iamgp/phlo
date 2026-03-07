"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from phlo.capabilities.specs import (
    AlertSinkSpec,
    AssetCheckSpec,
    AssetSpec,
    CatalogScannerSpec,
    CatalogSpec,
    DataMigrationSourceSpec,
    GovernanceBackendSpec,
    LineageSinkSpec,
    MaintenanceReadModelSpec,
    MetadataCatalogSpec,
    PublishTargetSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    ResourceSpec,
    SchemaMigrationSpec,
    SecretBackendSpec,
    TableStoreSpec,
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
    quality_backends: dict[str, QualityBackendSpec] = field(default_factory=dict)
    maintenance_read_models: dict[str, MaintenanceReadModelSpec] = field(default_factory=dict)
    metadata_catalogs: dict[str, MetadataCatalogSpec] = field(default_factory=dict)
    lineage_sinks: dict[str, LineageSinkSpec] = field(default_factory=dict)
    governance_backends: dict[str, GovernanceBackendSpec] = field(default_factory=dict)
    publish_targets: dict[str, PublishTargetSpec] = field(default_factory=dict)
    alert_sinks: dict[str, AlertSinkSpec] = field(default_factory=dict)
    secret_backends: dict[str, SecretBackendSpec] = field(default_factory=dict)
    schema_migrators: dict[str, SchemaMigrationSpec] = field(default_factory=dict)
    data_migration_sources: dict[str, DataMigrationSourceSpec] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def register_asset(self, spec: AssetSpec) -> None:
        """Register or replace an asset spec by key.

        Args:
            spec: Asset capability specification to store.
        """

        with self._lock:
            self.assets[spec.key] = spec

    def register_check(self, spec: AssetCheckSpec) -> None:
        """Register or replace an asset check spec by asset/name tuple.

        Args:
            spec: Asset check capability specification to store.
        """

        with self._lock:
            self.checks[(spec.asset_key, spec.name)] = spec

    def register_resource(self, spec: ResourceSpec) -> None:
        """Register or replace a resource spec by name.

        Args:
            spec: Resource capability specification to store.
        """

        with self._lock:
            self.resources[spec.name] = spec

    def list_assets(self) -> list[AssetSpec]:
        """Return a snapshot list of all registered assets.

        Returns:
            List of currently registered asset specs.
        """

        with self._lock:
            return list(self.assets.values())

    def list_checks(self) -> list[AssetCheckSpec]:
        """Return a snapshot list of all registered checks.

        Returns:
            List of currently registered asset check specs.
        """

        with self._lock:
            return list(self.checks.values())

    def list_resources(self) -> list[ResourceSpec]:
        """Return a snapshot list of all registered resources.

        Returns:
            List of currently registered resource specs.
        """

        with self._lock:
            return list(self.resources.values())

    def register_table_store(self, spec: TableStoreSpec) -> None:
        """Register or replace a table store spec by name."""
        with self._lock:
            self.table_stores[spec.name] = spec

    def list_table_stores(self) -> list[TableStoreSpec]:
        """Return a snapshot list of registered table store specs."""
        with self._lock:
            return list(self.table_stores.values())

    def register_catalog(self, spec: CatalogSpec) -> None:
        """Register or replace a catalog spec by name."""
        with self._lock:
            self.catalogs[spec.name] = spec

    def list_catalogs(self) -> list[CatalogSpec]:
        """Return a snapshot list of registered catalog specs."""
        with self._lock:
            return list(self.catalogs.values())

    def register_catalog_scanner(self, spec: CatalogScannerSpec) -> None:
        """Register or replace a catalog scanner spec by name."""
        with self._lock:
            self.catalog_scanners[spec.name] = spec

    def list_catalog_scanners(self) -> list[CatalogScannerSpec]:
        """Return a snapshot list of registered catalog scanner specs."""
        with self._lock:
            return list(self.catalog_scanners.values())

    def register_query_engine(self, spec: QueryEngineSpec) -> None:
        """Register or replace a query engine spec by name."""
        with self._lock:
            self.query_engines[spec.name] = spec

    def list_query_engines(self) -> list[QueryEngineSpec]:
        """Return a snapshot list of registered query engine specs."""
        with self._lock:
            return list(self.query_engines.values())

    def register_quality_backend(self, spec: QualityBackendSpec) -> None:
        """Register or replace a quality backend spec by name."""
        with self._lock:
            self.quality_backends[spec.name] = spec

    def list_quality_backends(self) -> list[QualityBackendSpec]:
        """Return a snapshot list of registered quality backend specs."""
        with self._lock:
            return list(self.quality_backends.values())

    def register_maintenance_read_model(self, spec: MaintenanceReadModelSpec) -> None:
        """Register or replace a maintenance read-model spec by name."""
        with self._lock:
            self.maintenance_read_models[spec.name] = spec

    def list_maintenance_read_models(self) -> list[MaintenanceReadModelSpec]:
        """Return a snapshot list of maintenance read-model specs."""
        with self._lock:
            return list(self.maintenance_read_models.values())

    def register_metadata_catalog(self, spec: MetadataCatalogSpec) -> None:
        """Register or replace a metadata catalog spec by name."""
        with self._lock:
            self.metadata_catalogs[spec.name] = spec

    def list_metadata_catalogs(self) -> list[MetadataCatalogSpec]:
        """Return a snapshot list of registered metadata catalog specs."""
        with self._lock:
            return list(self.metadata_catalogs.values())

    def register_lineage_sink(self, spec: LineageSinkSpec) -> None:
        """Register or replace a lineage sink spec by name."""
        with self._lock:
            self.lineage_sinks[spec.name] = spec

    def list_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Return a snapshot list of registered lineage sink specs."""
        with self._lock:
            return list(self.lineage_sinks.values())

    def register_governance_backend(self, spec: GovernanceBackendSpec) -> None:
        """Register or replace a governance backend spec by name."""
        with self._lock:
            self.governance_backends[spec.name] = spec

    def list_governance_backends(self) -> list[GovernanceBackendSpec]:
        """Return a snapshot list of registered governance backend specs."""
        with self._lock:
            return list(self.governance_backends.values())

    def register_publish_target(self, spec: PublishTargetSpec) -> None:
        """Register or replace a publish target spec by name."""
        with self._lock:
            self.publish_targets[spec.name] = spec

    def list_publish_targets(self) -> list[PublishTargetSpec]:
        """Return a snapshot list of registered publish target specs."""
        with self._lock:
            return list(self.publish_targets.values())

    def register_alert_sink(self, spec: AlertSinkSpec) -> None:
        """Register or replace an alert sink spec by name."""
        with self._lock:
            self.alert_sinks[spec.name] = spec

    def list_alert_sinks(self) -> list[AlertSinkSpec]:
        """Return a snapshot list of registered alert sink specs."""
        with self._lock:
            return list(self.alert_sinks.values())

    def register_secret_backend(self, spec: SecretBackendSpec) -> None:
        """Register or replace a secret backend spec by name."""
        with self._lock:
            self.secret_backends[spec.name] = spec

    def list_secret_backends(self) -> list[SecretBackendSpec]:
        """Return a snapshot list of registered secret backend specs."""
        with self._lock:
            return list(self.secret_backends.values())

    def register_schema_migrator(self, spec: SchemaMigrationSpec) -> None:
        """Register or replace a schema migrator spec by name."""
        with self._lock:
            self.schema_migrators[spec.name] = spec

    def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Return a snapshot list of registered schema migrator specs."""
        with self._lock:
            return list(self.schema_migrators.values())

    def register_data_migration_source(self, spec: DataMigrationSourceSpec) -> None:
        """Register or replace a data migration source adapter spec by name."""
        with self._lock:
            self.data_migration_sources[spec.name] = spec

    def list_data_migration_sources(self) -> list[DataMigrationSourceSpec]:
        """Return a snapshot list of registered migration source adapter specs."""
        with self._lock:
            return list(self.data_migration_sources.values())

    def clear(self) -> None:
        """Remove all assets, checks, and resources from the registry."""

        with self._lock:
            self.assets.clear()
            self.checks.clear()
            self.resources.clear()
            self.table_stores.clear()
            self.catalogs.clear()
            self.catalog_scanners.clear()
            self.query_engines.clear()
            self.quality_backends.clear()
            self.maintenance_read_models.clear()
            self.metadata_catalogs.clear()
            self.lineage_sinks.clear()
            self.governance_backends.clear()
            self.publish_targets.clear()
            self.alert_sinks.clear()
            self.secret_backends.clear()
            self.schema_migrators.clear()
            self.data_migration_sources.clear()

    def clear_checks(self) -> None:
        """Remove all registered checks while preserving assets/resources."""

        with self._lock:
            self.checks.clear()


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


def register_publish_target(spec: PublishTargetSpec) -> None:
    """Register a publish target in the process-global registry."""
    _GLOBAL_REGISTRY.register_publish_target(spec)


def register_alert_sink(spec: AlertSinkSpec) -> None:
    """Register an alert sink in the process-global registry."""
    _GLOBAL_REGISTRY.register_alert_sink(spec)


def register_secret_backend(spec: SecretBackendSpec) -> None:
    """Register a secret backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_secret_backend(spec)


def register_schema_migrator(spec: SchemaMigrationSpec) -> None:
    """Register a schema migrator in the process-global registry."""
    _GLOBAL_REGISTRY.register_schema_migrator(spec)


def register_data_migration_source(spec: DataMigrationSourceSpec) -> None:
    """Register a data migration source adapter in the process-global registry."""
    _GLOBAL_REGISTRY.register_data_migration_source(spec)


def clear_capabilities() -> None:
    """Clear all capability types from the global registry."""

    _GLOBAL_REGISTRY.clear()
