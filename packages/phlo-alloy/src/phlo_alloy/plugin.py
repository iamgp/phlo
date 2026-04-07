"""Alloy service plugin for Phlo platform integration.

This module implements the ServicePlugin interface for Grafana Alloy, enabling
automatic service discovery, lifecycle management, and configuration within the
Phlo observability stack. Alloy serves as the primary log collector and shipper,
sending logs to Loki for centralized aggregation and querying.

Classes:
    AlloyServicePlugin: Plugin implementation for Grafana Alloy service management.

Example:
    The plugin is auto-discovered via entry points and should not be instantiated
    directly. Configuration is loaded from ``service.yaml`` in the package resources::

        # This happens automatically via plugin discovery
        from phlo.plugins import discover_plugins
        plugins = discover_plugins()

See Also:
    - phlo.plugins.ServicePlugin: Base class for service plugins.
    - phlo.plugins.PluginMetadata: Metadata structure for plugin registration.
    - Grafana Alloy documentation: https://grafana.com/docs/alloy/latest/

Note:
    This plugin requires the ``pyyaml`` package for loading service definitions.

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class AlloyServicePlugin(PackageYamlServicePlugin):
    """Service plugin for Grafana Alloy log collection and shipping.

    This plugin manages the Grafana Alloy service lifecycle within the Phlo platform.
    Alloy collects logs from various sources and ships them to Loki for centralized
    storage and analysis. The plugin provides metadata for discovery and loads the
    service configuration from embedded YAML resources.

    Attributes:
        None: This class has no public attributes. All configuration is loaded
            dynamically from package resources.

    Example:
        The plugin is auto-discovered and should not be used directly::

            # Auto-discovery via entry points
            from phlo.plugins import discover_plugins
            plugin = discover_plugins().get("alloy")
            metadata = plugin.metadata
            service_def = plugin.service_definition

    See Also:
        phlo.plugins.ServicePlugin: Base class providing plugin interface.
        phlo.plugins.PluginMetadata: Metadata container for plugin information.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the Alloy service.

        Provides static metadata used by the Phlo plugin discovery system to
        identify and categorize the Alloy service plugin. This includes the
        plugin name, version, description, author information, and searchable tags.

        Returns:
            PluginMetadata: Static metadata containing:
                - name (str): Plugin identifier, "alloy".
                - version (str): Semantic version, "0.1.0".
                - description (str): Human-readable description of Alloy's purpose.
                - author (str): "Phlo Team".
                - tags (list[str]): Searchable tags ["observability", "logs", "agent"].

        Example:
            Metadata is accessed by the plugin discovery system::

                plugin = AlloyServicePlugin()
                meta = plugin.metadata
                print(f"{meta.name} v{meta.version}: {meta.description}")
                # Output: alloy v0.1.0: Grafana Alloy for log collection...

        Note:
            This property returns a new PluginMetadata instance on each access.
            The metadata is static and does not change at runtime.

        """
        return PluginMetadata(
            name="alloy",
            version="0.1.0",
            description="Grafana Alloy for log collection and shipping to Loki",
            author="Phlo Team",
            tags=["observability", "logs", "agent"],
        )
