"""Service package manifest resolution primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from phlo.plugins.discovery._service_definition import ServiceDefinition


def _is_service_yaml(filename: str) -> bool:
    return filename == "service.yaml" or filename.endswith(("-setup.yaml", "-daemon.yaml"))


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
