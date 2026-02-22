"""Service loading helpers for plugin and file-backed service definitions."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
from typing import Any

import yaml

from phlo.logging import get_logger
from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery.plugins import discover_plugins
from phlo.plugins.discovery.registry import get_global_registry

logger = get_logger(__name__)


def is_service_yaml(filename: str) -> bool:
    """Return True for recognized service definition YAML file names."""
    return filename == "service.yaml" or filename.endswith(("-setup.yaml", "-daemon.yaml"))


def load_plugin_services(services: dict[str, ServiceDefinition]) -> None:
    """Load service definitions from installed service plugins."""
    discover_plugins(plugin_type="services", auto_register=True)
    registry = get_global_registry()

    for name in registry.list_services():
        plugin = registry.get_service(name)
        if not plugin:
            continue
        if name in services:
            logger.debug("plugin_service_skipped_core_exists", service_name=name)
            continue

        service_definition = plugin.service_definition
        source_path = resolve_plugin_source_path(plugin)
        try:
            service = ServiceDefinition.from_dict(service_definition, source_path)
            services[service.name] = service
            load_companion_service_files(source_path, services)
        except KeyError as exc:
            logger.warning("Service plugin %s missing field: %s", name, exc)


def load_services_from_directory(
    services_dir: Path | None, services: dict[str, ServiceDefinition]
) -> None:
    """Load service definitions from a configured local services directory."""
    if not services_dir or not services_dir.exists():
        return

    for yaml_path in services_dir.rglob("*.yaml"):
        if ".schema" in str(yaml_path):
            continue
        if not is_service_yaml(yaml_path.name):
            continue

        try:
            service = ServiceDefinition.from_yaml(yaml_path)
            if service.name in services:
                continue
            services[service.name] = service
        except (yaml.YAMLError, KeyError) as exc:
            logger.warning("Failed to load %s: %s", yaml_path, exc)


def load_companion_service_files(
    source_path: Path | None, services: dict[str, ServiceDefinition]
) -> None:
    """Load companion service YAMLs (for example *-setup.yaml) from a package path."""
    if not source_path or not source_path.exists():
        return

    for yaml_path in source_path.rglob("*.yaml"):
        filename = yaml_path.name
        if filename == "service.yaml":
            continue
        if not filename.endswith(("-setup.yaml", "-daemon.yaml")):
            continue

        try:
            service = ServiceDefinition.from_yaml(yaml_path)
            if service.name in services:
                continue
            services[service.name] = service
        except (yaml.YAMLError, KeyError) as exc:
            logger.warning("Failed to load companion service %s: %s", yaml_path, exc)


def resolve_plugin_source_path(plugin: Any) -> Path | None:
    """Resolve plugin package path for companion service file discovery."""
    module_name = plugin.__class__.__module__
    package_name = module_name.split(".", 1)[0]
    spec = find_spec(package_name)
    if not spec or not spec.origin:
        return None
    return Path(spec.origin).parent
