"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec


@dataclass
class CapabilityRegistry:
    """Thread-safe in-memory registry for capability specifications."""

    assets: dict[str, AssetSpec] = field(default_factory=dict)
    checks: dict[tuple[str, str], AssetCheckSpec] = field(default_factory=dict)
    resources: dict[str, ResourceSpec] = field(default_factory=dict)
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

    def clear(self) -> None:
        """Remove all assets, checks, and resources from the registry."""

        with self._lock:
            self.assets.clear()
            self.checks.clear()
            self.resources.clear()

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


def clear_capabilities() -> None:
    """Clear all capability types from the global registry."""

    _GLOBAL_REGISTRY.clear()
