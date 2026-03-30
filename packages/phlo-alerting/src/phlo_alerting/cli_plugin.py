"""CLI plugin for alerting commands.

This module implements the CliCommandPlugin interface to expose alerting
management commands through the Phlo CLI. It integrates the alerts command
group into the main Phlo command structure.

Examples:
    The plugin is automatically discovered and loaded by Phlo's CLI:
        $ phlo alerts test
        $ phlo alerts list
        $ phlo alerts status

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_alerting.cli_alerts import alerts_group


class AlertingCliPlugin(CliCommandPlugin):
    """Expose alerting commands to the Phlo CLI plugin system.

    CLI plugin implementation that registers the alerts command group
    with the Phlo CLI. Provides commands for testing, listing, and
    checking the status of alert destinations.

    Attributes:
        metadata: Plugin identity and discovery information.

    Examples:
        >>> plugin = AlertingCliPlugin()
        >>> plugin.metadata.name
        'alerts'
        >>> commands = plugin.get_cli_commands()
        >>> len(commands)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin identity metadata for discovery.

        Returns:
            PluginMetadata containing name, version, and description
            for CLI plugin registration.

        Examples:
            >>> plugin = AlertingCliPlugin()
            >>> meta = plugin.metadata
            >>> meta.name
            'alerts'
            >>> meta.version
            '0.1.0'

        """
        return PluginMetadata(
            name="alerts",
            version="0.1.0",
            description="Alerting CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by the alerting plugin.

        Returns the Click command group containing all alerting subcommands.
        This group is registered with the main Phlo CLI.

        Returns:
            Ordered list of alerting Click commands (currently just alerts_group).

        Examples:
            >>> plugin = AlertingCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> len(commands)
            1
            >>> commands[0].name
            'alerts'

        """
        return [alerts_group]
