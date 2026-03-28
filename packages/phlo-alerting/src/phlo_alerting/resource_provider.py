"""Resource provider plugin for phlo-alerting capabilities.

This module implements the ResourceProviderPlugin interface to expose
phlo-alerting as a neutral alert sink capability within the Phlo plugin
system. It enables other plugins to discover and use alerting functionality
through standardized capability contracts.

Examples:
    The plugin is automatically discovered by Phlo's plugin system:
        >>> from phlo.plugins import discover_plugins
        >>> plugins = discover_plugins()
        >>> # AlertingResourceProvider is registered automatically

"""

from __future__ import annotations

from phlo.capabilities import AlertSinkSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_alerting.alert_sink import AlertManagerSink


class AlertingResourceProvider(ResourceProviderPlugin):
    """Expose phlo-alerting as a neutral alert sink capability.

    This resource provider registers phlo-alerting with the Phlo capability
    system, allowing other components to discover and use alerting
    functionality through the AlertSinkSpec contract.

    Attributes:
        metadata: Plugin identity and discovery information.

    Examples:
        >>> provider = AlertingResourceProvider()
        >>> provider.metadata.name
        'alerting'
        >>> sinks = provider.get_alert_sinks()
        >>> len(sinks)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery.

        Returns:
            PluginMetadata containing name, version, description, and tags.

        Examples:
            >>> provider = AlertingResourceProvider()
            >>> meta = provider.metadata
            >>> meta.name
            'alerting'
            >>> meta.version
            '0.1.0'

        """
        return PluginMetadata(
            name="alerting",
            version="0.1.0",
            description="Alert sink capability provider",
            tags=["alerting"],
        )

    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly;
        alerting functionality is exposed through get_alert_sinks().

        Returns:
            Empty list since no raw resources are exposed.

        Examples:
            >>> provider = AlertingResourceProvider()
            >>> provider.get_resources()
            []

        """
        return []

    def get_alert_sinks(self) -> list[AlertSinkSpec]:
        """Expose phlo-alerting as an alert sink capability.

        Returns a list of AlertSinkSpec objects that define how other
        components can send alerts through this provider.

        Returns:
            List containing a single AlertSinkSpec for the alerting capability.

        Examples:
            >>> provider = AlertingResourceProvider()
            >>> sinks = provider.get_alert_sinks()
            >>> len(sinks)
            1
            >>> sinks[0].name
            'alerting'

        """
        return [
            AlertSinkSpec(
                name="alerting",
                provider=AlertManagerSink(),
            )
        ]
