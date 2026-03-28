"""CLI plugin for Sling commands.

This module provides the CLI plugin implementation that exposes Sling-related
commands to the Phlo command-line interface. It integrates with Phlo's plugin
system to add Sling replication management commands.

Classes:
    SlingCliPlugin: CLI plugin implementation for Sling commands.

Example:
    The plugin is automatically discovered::

        # In your shell
        $ phlo sling --help
        $ phlo sling run --source PHLO_POSTGRES --stream public.users --target PHLO_S3

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_sling.cli_commands import sling_group


class SlingCliPlugin(CliCommandPlugin):
    """Expose Sling CLI command groups to the Phlo plugin system.

    This plugin class provides Sling-related CLI commands to the Phlo
    command-line interface. It exposes commands for running replications,
    listing connections, and discovering available streams.

    Attributes:
        metadata (PluginMetadata): Information about this plugin including
            name, version, and description.

    Example:
        Commands are accessed via the ``phlo sling`` group::

            $ phlo sling run --help
            $ phlo sling conns --auto
            $ phlo sling discover PHLO_POSTGRES --schema public

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata containing name, version, and description of
            this Sling CLI plugin.

        """
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling replication CLI commands for Phlo",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns the list of Click command groups exposed by this plugin.
        These commands are mounted under the ``phlo`` CLI as subcommands.

        Returns:
            List of Click Command objects contributed by this plugin.

        """
        return [sling_group]
