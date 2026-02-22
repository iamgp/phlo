"""Service discovery orchestration over plugins and YAML definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery._service_dependency_resolution import resolve_service_dependencies
from phlo.plugins.discovery._service_loading import (
    is_service_yaml,
    load_companion_service_files,
    load_plugin_services,
    load_services_from_directory,
)


class ServiceDiscovery:
    """Discovers and manages service definitions."""

    def __init__(self, services_dir: Path | None = None):
        """Initialize with an optional services directory."""
        self.services_dir = services_dir
        self._services: dict[str, ServiceDefinition] = {}
        self._loaded = False

    def discover(self, refresh: bool = False) -> dict[str, ServiceDefinition]:
        """Discover all service definitions."""
        if refresh:
            self.clear_cache()

        if self._loaded:
            return self._services

        self._services = {}
        self._load_service_plugins()
        load_services_from_directory(self.services_dir, self._services)

        self._loaded = True
        return self._services

    def clear_cache(self) -> None:
        """Clear cached discovery state."""
        self._services = {}
        self._loaded = False

    def refresh(self) -> dict[str, ServiceDefinition]:
        """Force rediscovery and return refreshed service definitions."""
        return self.discover(refresh=True)

    def _load_service_plugins(self) -> None:
        """Load services from installed plugins."""
        load_plugin_services(self._services)

    @staticmethod
    def _is_service_yaml(filename: str) -> bool:
        """Check if filename is a recognized service YAML pattern."""
        return is_service_yaml(filename)

    def _load_companion_service_files(self, source_path: Path | None) -> None:
        """Load companion service YAMLs from a package."""
        load_companion_service_files(source_path, self._services)

    def get_service(self, name: str) -> ServiceDefinition | None:
        """Get a service definition by name."""
        self.discover()
        return self._services.get(name)

    def get_default_services(
        self, disabled_services: set[str] | None = None
    ) -> list[ServiceDefinition]:
        """Get all services marked as default, excluding disabled ones."""
        self.discover()
        disabled = disabled_services or set()
        return [
            service
            for service in self._services.values()
            if service.default and service.name not in disabled
        ]

    def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
        """Get all services in a specific profile."""
        self.discover()
        return [service for service in self._services.values() if service.profile == profile]

    def get_services_by_category(self, category: str) -> list[ServiceDefinition]:
        """Get all services in a specific category."""
        self.discover()
        return [service for service in self._services.values() if service.category == category]

    def get_available_profiles(self) -> set[str]:
        """Get all available profile names."""
        self.discover()
        return {service.profile for service in self._services.values() if service.profile}

    def resolve_dependencies(self, services: list[ServiceDefinition]) -> list[ServiceDefinition]:
        """Resolve and sort services by dependencies (topological sort)."""
        self.discover()
        return resolve_service_dependencies(services)

    def list_all(self) -> list[dict[str, Any]]:
        """List all services with selected metadata."""
        self.discover()
        return [
            {
                "name": service.name,
                "description": service.description,
                "category": service.category,
                "default": service.default,
                "profile": service.profile,
                "depends_on": service.depends_on,
            }
            for service in sorted(
                self._services.values(), key=lambda item: (item.category, item.name)
            )
        ]
