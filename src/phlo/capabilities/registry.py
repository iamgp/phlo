"""Capability registry for assets, checks, and resources."""

from __future__ import annotations

from dataclasses import dataclass, field

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec


@dataclass
class CapabilityRegistry:
    assets: dict[str, AssetSpec] = field(default_factory=dict)
    checks: list[AssetCheckSpec] = field(default_factory=list)
    resources: dict[str, ResourceSpec] = field(default_factory=dict)

    def register_asset(self, spec: AssetSpec) -> None:
        self.assets[spec.key] = spec

    def register_check(self, spec: AssetCheckSpec) -> None:
        self.checks.append(spec)

    def register_resource(self, spec: ResourceSpec) -> None:
        self.resources[spec.name] = spec

    def list_assets(self) -> list[AssetSpec]:
        return list(self.assets.values())

    def list_checks(self) -> list[AssetCheckSpec]:
        return list(self.checks)

    def list_resources(self) -> list[ResourceSpec]:
        return list(self.resources.values())

    def clear(self) -> None:
        self.assets.clear()
        self.checks.clear()
        self.resources.clear()


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
