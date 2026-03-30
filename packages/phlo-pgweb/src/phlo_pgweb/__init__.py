"""Pgweb package for Phlo.

This package provides a web-based PostgreSQL database browser service plugin
for the Phlo data platform. It integrates pgweb (a lightweight web-based
PostgreSQL admin tool) as a service that can be managed through Phlo's
plugin system.

Example:
    The plugin is automatically discovered by Phlo's plugin system:

    >>> from phlo.plugins import discover_plugins
    >>> plugins = discover_plugins()
    >>> pgweb = plugins.get("pgweb")

Attributes:
    __version__: Package version string.

"""

__version__ = "0.1.0"
