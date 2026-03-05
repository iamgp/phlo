"""
Service plugin classes.

This module defines plugin types for Docker-based infrastructure components.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from phlo.plugins.base.plugin import Plugin


class ServicePlugin(Plugin, ABC):
    """
    Base class for service plugins.

    Service plugins provide Docker-based infrastructure components
    that can be composed into a Phlo stack.
    """

    @property
    @abstractmethod
    def service_definition(self) -> dict[str, Any]:
        """
        Return the service definition.

        This is equivalent to the content of a service.yaml file.
        """

    @property
    def category(self) -> str:
        """Service category (core, api, bi, observability, etc.)."""
        return self.service_definition.get("category", "custom")

    @property
    def is_default(self) -> bool:
        """Whether this service should be installed by default."""
        return self.service_definition.get("default", False)

    @property
    def profile(self) -> str | None:
        """Optional profile this service belongs to."""
        return self.service_definition.get("profile")

    def get_compose_fragment(self) -> dict[str, Any]:
        """Return Docker Compose service configuration."""
        return self.service_definition.get("compose", {})

    def get_files(self) -> list[dict[str, str]]:
        """Return files to copy during initialization."""
        return self.service_definition.get("files", [])

    def get_dependencies(self) -> list[str]:
        """Return list of service names this depends on."""
        return self.service_definition.get("depends_on", [])

    @property
    def requires_capabilities(self) -> list[str]:
        """Return required capabilities for this service plugin."""
        return list(self.metadata.requires_capabilities)

    @property
    def optional_capabilities(self) -> list[str]:
        """Return optional capabilities for this service plugin."""
        return list(self.metadata.optional_capabilities)
