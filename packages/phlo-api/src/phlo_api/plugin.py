"""Phlo API service plugin.

This module provides the ServicePlugin implementation for the Phlo API backend,
integrating with the phlo plugin system to register the API service definition.

Classes:
    PhloApiServicePlugin: Service plugin for the Phlo API backend.

Example:
    The plugin is automatically discovered and loaded by the phlo plugin system:

    .. code-block:: python

        from phlo.plugins.discovery import ServiceDiscovery

        discovery = ServiceDiscovery()
        service = discovery.get_service("phlo-api")
        print(service.name)  # "phlo-api"

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class PhloApiServicePlugin(PackageYamlServicePlugin):
    """Service plugin for the Phlo API backend.

    This plugin registers the Phlo API as a discoverable service within
    the phlo ecosystem. It provides metadata about the service and
    exposes the Docker Compose service definition.

    The plugin reads its service definition from the embedded service.yaml
    file within the phlo_api package.

    Attributes:
        metadata: Plugin metadata including name, version, and description.
        service_definition: Docker Compose service configuration dict.

    Example:
        .. code-block:: python

            plugin = PhloApiServicePlugin()
            meta = plugin.metadata
            print(f"{meta.name} v{meta.version}")

            service_def = plugin.service_definition
            print(service_def["services"]["phlo-api"]["image"])

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Phlo API service.

        Returns:
            PluginMetadata: Metadata containing name, version, description,
                author, and tags for the plugin.

        Example:
            .. code-block:: python

                plugin = PhloApiServicePlugin()
                meta = plugin.metadata
                assert meta.name == "phlo-api"
                assert "api" in meta.tags

        """
        return PluginMetadata(
            name="phlo-api",
            version="0.1.0",
            description="Backend API exposing Phlo internals to Observatory",
            author="Phlo Team",
            tags=["api", "observability"],
        )
