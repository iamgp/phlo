"""Service and resource provider plugins for Trino."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.capabilities import ResourceSpec
from phlo.capabilities.specs import GovernanceBackendSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin, ServicePlugin
from phlo_trino.governance import TrinoGovernanceBackend
from phlo_trino.resource import TrinoResource


class TrinoServicePlugin(ServicePlugin):
    """Service plugin for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Trino service registration.

        Returns:
            Plugin metadata used by plugin discovery.
        """
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Distributed SQL query engine",
            author="Phlo Team",
            tags=["core", "query"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load the Trino service compose definition.

        Returns:
            Parsed service definition from `service.yaml`.
        """
        service_path = resources.files("phlo_trino").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))


class TrinoResourceProvider(ResourceProviderPlugin):
    """Resource provider plugin for Trino."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Trino resource registration.

        Returns:
            Plugin metadata used by plugin discovery.
        """
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="Trino resource for Phlo",
        )

    def get_resources(self) -> list[ResourceSpec]:
        """Return Trino resources exposed by this plugin.

        Returns:
            Resource specifications for Trino integrations.
        """
        return [ResourceSpec(name="trino", resource=TrinoResource())]

    def get_governance_backends(self) -> list[GovernanceBackendSpec]:
        """Return Trino governance backend specs.

        Returns:
            Governance backend specifications for Trino SQL grants.
        """
        return [GovernanceBackendSpec(name="trino", provider=TrinoGovernanceBackend())]
