"""Capability primitives and registry."""

from phlo.capabilities.registry import (
    CapabilityRegistry,
    clear_capabilities,
    get_capability_registry,
    register_asset,
    register_check,
    register_resource,
)
from phlo.capabilities.runtime import RuntimeContext
from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CheckResult,
    MaterializeResult,
    PartitionSpec,
    ResourceSpec,
    RunResult,
    RunSpec,
)

__all__ = [
    "AssetCheckSpec",
    "AssetSpec",
    "CapabilityRegistry",
    "CheckResult",
    "MaterializeResult",
    "PartitionSpec",
    "ResourceSpec",
    "RunResult",
    "RunSpec",
    "RuntimeContext",
    "clear_capabilities",
    "get_capability_registry",
    "register_asset",
    "register_check",
    "register_resource",
]
