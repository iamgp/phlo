"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec


@dataclass
class CapabilityRegistry:
    assets: dict[str, AssetSpec] = field(default_factory=dict)
    checks: dict[tuple[str, str], AssetCheckSpec] = field(default_factory=dict)
    resources: dict[str, ResourceSpec] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def register_asset(self, spec: AssetSpec) -> None:
        with self._lock:
            self.assets[spec.key] = spec

    def register_check(self, spec: AssetCheckSpec) -> None:
        with self._lock:
            self.checks[(spec.asset_key, spec.name)] = spec

    def register_resource(self, spec: ResourceSpec) -> None:
        with self._lock:
            self.resources[spec.name] = spec

    def list_assets(self) -> list[AssetSpec]:
        with self._lock:
            return list(self.assets.values())

    def list_checks(self) -> list[AssetCheckSpec]:
        with self._lock:
            return list(self.checks.values())

    def list_resources(self) -> list[ResourceSpec]:
        with self._lock:
            return list(self.resources.values())

    def clear(self) -> None:
        with self._lock:
            self.assets.clear()
            self.checks.clear()
            self.resources.clear()

    def clear_checks(self) -> None:
        with self._lock:
            self.checks.clear()


_GLOBAL_REGISTRY = CapabilityRegistry()


def get_capability_registry() -> CapabilityRegistry:
    return _GLOBAL_REGISTRY


def register_asset(spec: AssetSpec) -> None:
    _GLOBAL_REGISTRY.register_asset(spec)


def register_check(spec: AssetCheckSpec) -> None:
    _GLOBAL_REGISTRY.register_check(spec)


def register_resource(spec: ResourceSpec) -> None:
    _GLOBAL_REGISTRY.register_resource(spec)


def clear_capabilities() -> None:
    _GLOBAL_REGISTRY.clear()
