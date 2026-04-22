"""oauth2-proxy service plugin implementation."""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class Oauth2ProxyServicePlugin(PackageYamlServicePlugin):
    """Service plugin for oauth2-proxy authentication gateway.

    This plugin provides integration with oauth2-proxy, an OAuth2/OIDC
    authentication proxy that implements forward-auth with Traefik.
    It reads service configuration from a bundled service.yaml file
    and exposes standard Phlo plugin metadata.

    Attributes:
        None

    Example:
        >>> plugin = Oauth2ProxyServicePlugin()
        >>> metadata = plugin.metadata
        >>> print(metadata.name, metadata.version)
        oauth2-proxy 0.1.0
        >>> definition = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the oauth2-proxy service.

        Returns:
            PluginMetadata: Plugin metadata containing name, version,
                description, author, and tags.

        Example:
            >>> plugin = Oauth2ProxyServicePlugin()
            >>> meta = plugin.metadata
            >>> meta.name
            'oauth2-proxy'
            >>> meta.tags
            ['auth', 'proxy', 'oidc']

        """
        return PluginMetadata(
            name="oauth2-proxy",
            version="0.1.0",
            description="OAuth2/OIDC authentication proxy for Phlo services",
            author="Phlo Team",
            tags=["auth", "proxy", "oidc"],
        )
