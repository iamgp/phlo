"""Service discovery public compatibility layer."""

from __future__ import annotations

from phlo.plugins.discovery._service_cycles import find_cycles as _find_cycles_impl
from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery._service_discovery import ServiceDiscovery
from phlo.plugins.discovery._service_loading import (
    is_service_yaml as _is_service_yaml_impl,
)
from phlo.plugins.discovery._service_loading import (
    resolve_plugin_source_path as _resolve_plugin_source_path_impl,
)

_find_cycles = _find_cycles_impl
_is_service_yaml = _is_service_yaml_impl
_resolve_plugin_source_path = _resolve_plugin_source_path_impl

__all__ = [
    "ServiceDefinition",
    "ServiceDiscovery",
]
