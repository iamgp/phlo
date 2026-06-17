"""Openmetadata CLI plugin registration."""

from __future__ import annotations

from phlo.plugins.base import cli_command_plugin_class

from phlo_openmetadata.cli_openmetadata import openmetadata


OpenMetadataCliPlugin = cli_command_plugin_class(
    "OpenMetadataCliPlugin",
    name="openmetadata",
    version="0.1.0",
    description="CLI commands for OpenMetadata synchronization",
    commands=[openmetadata],
)
