"""Phlo Prometheus monitoring package.

This package provides Prometheus service integration for the Phlo data platform,
enabling metrics collection and monitoring capabilities.

Example:
    The package is loaded automatically by the Phlo plugin system::

        from phlo.plugins import load_plugin
        plugin = load_plugin("prometheus")
        definition = plugin.service_definition

Attributes:
    __version__: Package version string.

"""

__version__ = "0.1.0"
