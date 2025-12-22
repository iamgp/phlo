"""
Service Discovery Module

Discovers and loads service definitions from the services/ directory.
"""

import logging
from importlib.util import find_spec
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from phlo.plugins.discovery import discover_plugins
from phlo.plugins.registry import get_global_registry

logger = logging.getLogger(__name__)


@dataclass
class ServiceDefinition:
    """Represents a parsed service.yaml definition."""

    name: str
    description: str
    category: str = "core"
    version: str = "latest"
    default: bool = False
    profile: str | None = None
    depends_on: list[str] = field(default_factory=list)
    image: str | None = None
    build: dict[str, Any] | None = None
    compose: dict[str, Any] = field(default_factory=dict)
    env_vars: dict[str, dict[str, Any]] = field(default_factory=dict)
    files: list[dict[str, str]] = field(default_factory=list)
    hooks: dict[str, str] = field(default_factory=dict)
    source_path: Path | None = None
    phlo_dev: bool = False  # Services that receive phlo source mount in dev mode

    @classmethod
    def from_yaml(cls, path: Path) -> "ServiceDefinition":
        """Load a service definition from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            name=data["name"],
            description=data["description"],
            category=data.get("category", "core"),
            version=data.get("version", "latest"),
            default=data.get("default", False),
            profile=data.get("profile"),
            depends_on=data.get("depends_on", []),
            image=data.get("image"),
            build=data.get("build"),
            compose=data.get("compose", {}),
            env_vars=data.get("env_vars", {}),
            files=data.get("files", []),
            hooks=data.get("hooks", {}),
            source_path=path.parent,
            phlo_dev=data.get("phlo_dev", False),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path | None) -> "ServiceDefinition":
        """Load a service definition from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "core"),
            version=data.get("version", "latest"),
            default=data.get("default", False),
            profile=data.get("profile"),
            depends_on=data.get("depends_on", []),
            image=data.get("image"),
            build=data.get("build"),
            compose=data.get("compose", {}),
            env_vars=data.get("env_vars", {}),
            files=data.get("files", []),
            hooks=data.get("hooks", {}),
            source_path=source_path,
            phlo_dev=data.get("phlo_dev", False),
        )


class ServiceDiscovery:
    """Discovers and manages service definitions."""

    def __init__(self, services_dir: Path | None = None):
        """Initialize with services directory path.

        Args:
            services_dir: Path to services/ directory. If None, uses the
                         bundled services in the phlo package.
        """
        if services_dir is None:
            # Use bundled services from phlo package
            services_dir = Path(__file__).parent.parent.parent.parent / "services"

        self.services_dir = services_dir
        self._services: dict[str, ServiceDefinition] = {}
        self._loaded = False

    def discover(self) -> dict[str, ServiceDefinition]:
        """Discover all service definitions.

        Returns:
            Dictionary mapping service names to their definitions.
        """
        if self._loaded:
            return self._services

        self._services = {}

        if not self.services_dir.exists():
            self._load_service_plugins()
            self._loaded = True
            return self._services

        self._load_service_plugins()

        # Search for service.yaml files in all subdirectories
        for yaml_path in self.services_dir.rglob("*.yaml"):
            # Skip schema files
            if ".schema" in str(yaml_path):
                continue

            # Skip non-service files
            if yaml_path.name not in ("service.yaml",) and not yaml_path.name.endswith(
                "-daemon.yaml"
            ):
                # Also load companion services like minio-setup.yaml, dagster-daemon.yaml
                if not any(
                    yaml_path.name.endswith(suffix) for suffix in ("-setup.yaml", "-daemon.yaml")
                ):
                    continue

            try:
                service = ServiceDefinition.from_yaml(yaml_path)
                if service.name in self._services:
                    continue
                self._services[service.name] = service
            except (yaml.YAMLError, KeyError) as e:
                logger.warning("Failed to load %s: %s", yaml_path, e)

        self._loaded = True
        return self._services

    def _load_service_plugins(self) -> None:
        discover_plugins(plugin_type="services", auto_register=True)
        registry = get_global_registry()
        for name in registry.list_services():
            plugin = registry.get_service(name)
            if not plugin:
                continue
            service_definition = plugin.service_definition
            source_path = _resolve_plugin_source_path(plugin)
            try:
                service = ServiceDefinition.from_dict(service_definition, source_path)
                self._services[service.name] = service
            except KeyError as exc:
                logger.warning("Service plugin %s missing field: %s", name, exc)


def _resolve_plugin_source_path(plugin: Any) -> Path | None:
    module_name = plugin.__class__.__module__
    package_name = module_name.split(".", 1)[0]
    spec = find_spec(package_name)
    if not spec or not spec.origin:
        return None
    return Path(spec.origin).parent

    def get_service(self, name: str) -> ServiceDefinition | None:
        """Get a service definition by name."""
        self.discover()
        return self._services.get(name)

    def get_default_services(self) -> list[ServiceDefinition]:
        """Get all services marked as default."""
        self.discover()
        return [s for s in self._services.values() if s.default]

    def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
        """Get all services in a specific profile."""
        self.discover()
        return [s for s in self._services.values() if s.profile == profile]

    def get_services_by_category(self, category: str) -> list[ServiceDefinition]:
        """Get all services in a specific category."""
        self.discover()
        return [s for s in self._services.values() if s.category == category]

    def get_available_profiles(self) -> set[str]:
        """Get all available profile names."""
        self.discover()
        return {s.profile for s in self._services.values() if s.profile}

    def resolve_dependencies(self, services: list[ServiceDefinition]) -> list[ServiceDefinition]:
        """Resolve and sort services by dependencies (topological sort).

        Args:
            services: List of services to sort.

        Returns:
            List of services in dependency order (dependencies first).

        Raises:
            ValueError: If circular dependencies are detected.
        """
        self.discover()

        # Build dependency graph
        service_names = {s.name for s in services}
        graph: dict[str, set[str]] = {}
        in_degree: dict[str, int] = {}

        for service in services:
            graph[service.name] = set()
            in_degree[service.name] = 0

        for service in services:
            for dep in service.depends_on:
                if dep in service_names:
                    graph[dep].add(service.name)
                    in_degree[service.name] += 1

        # Kahn's algorithm for topological sort
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(services):
            # Circular dependency detected
            remaining = set(in_degree.keys()) - set(result)
            raise ValueError(f"Circular dependency detected among: {remaining}")

        # Return services in sorted order
        name_to_service = {s.name: s for s in services}
        return [name_to_service[name] for name in result]

    def list_all(self) -> list[dict[str, Any]]:
        """List all services with their metadata.

        Returns:
            List of service info dictionaries.
        """
        self.discover()
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "default": s.default,
                "profile": s.profile,
                "depends_on": s.depends_on,
            }
            for s in sorted(self._services.values(), key=lambda x: (x.category, x.name))
        ]
