"""Service package manifest resolution primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from phlo.plugins.discovery._service_definition import ServiceDefinition


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
