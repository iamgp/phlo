"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CatalogSpec,
    LineageSinkSpec,
    MetadataCatalogSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    ResourceSpec,
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
    query_engines: dict[str, QueryEngineSpec] = field(default_factory=dict)
    quality_backends: dict[str, QualityBackendSpec] = field(default_factory=dict)
    metadata_catalogs: dict[str, MetadataCatalogSpec] = field(default_factory=dict)
    lineage_sinks: dict[str, LineageSinkSpec] = field(default_factory=dict)
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

    def clear(self) -> None:
        """Remove all assets, checks, and resources from the registry."""

        with self._lock:
            self.assets.clear()
            self.checks.clear()
            self.resources.clear()
            self.table_stores.clear()
            self.catalogs.clear()
            self.query_engines.clear()
            self.quality_backends.clear()
            self.metadata_catalogs.clear()
            self.lineage_sinks.clear()

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


def register_query_engine(spec: QueryEngineSpec) -> None:
    """Register a query engine in the process-global registry."""
    _GLOBAL_REGISTRY.register_query_engine(spec)


def register_quality_backend(spec: QualityBackendSpec) -> None:
    """Register a quality backend in the process-global registry."""
    _GLOBAL_REGISTRY.register_quality_backend(spec)


def register_metadata_catalog(spec: MetadataCatalogSpec) -> None:
    """Register a metadata catalog in the process-global registry."""
    _GLOBAL_REGISTRY.register_metadata_catalog(spec)


def register_lineage_sink(spec: LineageSinkSpec) -> None:
    """Register a lineage sink in the process-global registry."""
    _GLOBAL_REGISTRY.register_lineage_sink(spec)


def clear_capabilities() -> None:
    """Clear all capability types from the global registry."""

    _GLOBAL_REGISTRY.clear()
