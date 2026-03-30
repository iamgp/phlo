"""Grafana observability package for Phlo.

This package provides Grafana integration for the Phlo observability stack,
offering metrics visualization, dashboard management, and service integration
capabilities. Grafana serves as the primary visualization layer for metrics
collected by Prometheus and other observability components.

Example:
    The package is auto-discovered via the phlo-grafana entry point:

    >>> from phlo.plugins import discover_plugins
    >>> plugins = discover_plugins()
    >>> grafana_plugin = plugins.get("grafana")

Attributes:
    __version__: Package version string.

"""

__version__ = "0.1.0"
