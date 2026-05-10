"""Service package manifest resolution primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery._service_loading import resolve_plugin_source_path
from phlo.plugins.discovery.plugins import discover_plugins
from phlo.plugins.discovery.registry import get_global_registry


def _is_service_yaml(filename: str) -> bool:
    return filename == "service.yaml" or filename.endswith(("-setup.yaml", "-daemon.yaml"))


def get_registered_service_plugins() -> dict[str, Any]:
    registry = get_global_registry()
    return {
        name: plugin
        for name in registry.list_services()
        if (plugin := registry.get_service(name)) is not None
    }


def _companion_manifests(
    source_path: Path | None,
    existing_names: set[str],
) -> list[ServiceManifest]:
    if not source_path or not source_path.exists():
        return []

    manifests: list[ServiceManifest] = []
    for yaml_path in sorted(source_path.rglob("*.yaml")):
        if yaml_path.name == "service.yaml":
            continue
        if not yaml_path.name.endswith(("-setup.yaml", "-daemon.yaml")):
            continue
        definition = ServiceDefinition.from_yaml(yaml_path)
        if definition.name in existing_names:
            continue
        existing_names.add(definition.name)
        manifests.append(ServiceManifest(definition=definition, source_path=yaml_path))
    return manifests


class ServiceManifestError(ValueError):
    """Raised when a service package manifest cannot be resolved."""

    def __init__(
        self,
        message: str,
        *,
        service_name: str | None = None,
        source_path: Path | None = None,
    ) -> None:
        self.message = message
        self.service_name = service_name
        self.source_path = source_path
        super().__init__(self.__str__())

    def __str__(self) -> str:
        details: list[str] = []
        if self.service_name:
            details.append(f"service={self.service_name}")
        if self.source_path:
            details.append(f"source={self.source_path}")
        if not details:
            return self.message
        return f"{self.message}: {' '.join(details)}"


@dataclass(frozen=True, slots=True)
class ServiceManifest:
    """Resolved service package manifest with source context."""

    definition: ServiceDefinition
    source_path: Path | None = None

    @property
    def name(self) -> str:
        return self.definition.name


@dataclass(slots=True)
class ServiceManifestResolver:
    """Resolve service package manifests from plugins and local service directories."""

    services_dir: Path | None = None

    def resolve_plugin_manifests(self) -> list[ServiceManifest]:
        discover_plugins(plugin_type="services", auto_register=True)
        manifests: list[ServiceManifest] = []
        names: set[str] = set()
        for name, plugin in get_registered_service_plugins().items():
            source_path = resolve_plugin_source_path(plugin)
            try:
                definition = ServiceDefinition.from_dict(plugin.service_definition, source_path)
            except (KeyError, ValueError) as exc:
                raise ServiceManifestError(
                    "invalid plugin service definition",
                    service_name=name,
                    source_path=source_path,
                ) from exc
            if definition.name in names:
                continue
            names.add(definition.name)
            manifests.append(ServiceManifest(definition=definition, source_path=source_path))
            manifests.extend(_companion_manifests(source_path, names))
        return manifests

    def resolve_directory_manifests(self) -> list[ServiceManifest]:
        if not self.services_dir or not self.services_dir.exists():
            return []

        manifests: list[ServiceManifest] = []
        for yaml_path in sorted(self.services_dir.rglob("*.yaml")):
            if ".schema" in str(yaml_path):
                continue
            if not _is_service_yaml(yaml_path.name):
                continue
            try:
                definition = ServiceDefinition.from_yaml(yaml_path)
            except (yaml.YAMLError, KeyError, ValueError) as exc:
                raise ServiceManifestError(
                    "invalid service definition file",
                    source_path=yaml_path,
                ) from exc
            manifests.append(ServiceManifest(definition=definition, source_path=yaml_path))
        return manifests
