"""Phlo Loki logging package.

This package provides a Loki logging service integration for the Phlo data platform,
including a Docker Compose service definition and an Observatory UI extension for
log viewing and querying.

Modules:
    plugin: Service plugin for Loki container orchestration.
    observatory_plugin: Observatory UI extension for log visualization.

Example:
    Service plugin is auto-discovered by Phlo plugin system::

        from phlo.plugins import load_plugin
        plugin = load_plugin("phlo_loki")

"""
