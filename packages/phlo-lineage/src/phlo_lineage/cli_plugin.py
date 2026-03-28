"""CLI plugin for lineage commands.

This module provides the LineageCliPlugin class, which registers the lineage
CLI command group with the Phlo plugin system. It exposes all lineage-related
commands (show, export, impact, status, column) through the main phlo CLI.

Commands Exposed:
    - lineage show: Display ASCII tree lineage visualization
    - lineage export: Export to DOT, Mermaid, or JSON formats
    - lineage impact: Analyze downstream impact of changes
    - lineage status: Display graph statistics
    - lineage column import-dbt: Import column lineage from dbt manifests
    - lineage column upstream/downstream: Query column-level lineage

Plugin Registration:
    This plugin is auto-discovered via the phlo.cli_commands entry point.
    No manual registration required.

Command Structure:
    phlo lineage
    ├── show          # Visualize asset dependencies
    ├── export        # Export to external formats
    ├── impact        # Analyze change impact
    ├── status        # Graph statistics
    └── column
        ├── import-dbt  # Import from dbt manifest
        ├── upstream    # Query upstream columns
        └── downstream  # Query downstream columns

Example:
    After plugin registration, commands are available via:

    $ phlo lineage show orders
    $ phlo lineage export orders --format dot --output lineage.dot
    $ phlo lineage impact silver.stg_orders
    $ phlo lineage status

See Also:
    phlo_lineage.cli_lineage for command implementations.
    phlo.plugins.base.CliCommandPlugin for the plugin interface.

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_lineage.cli_lineage import lineage_group


class LineageCliPlugin(CliCommandPlugin):
    """Register lineage CLI commands with the plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

                Provides identifying information for the Phlo CLI plugin system
        to recognize and load this command provider.

        Returns:
                    PluginMetadata with CLI plugin identity:
                        - name: "lineage" (identifier for plugin system)
                        - version: "0.1.0" (semantic version)
                        - description: "Lineage CLI commands" (brief description)

                Discovery:
                    This metadata is used by the CLI framework to:
                    - Identify the plugin uniquely
                    - Display plugin information in help text
                    - Enable plugin introspection and debugging

        Example:
                    >>> plugin = LineageCliPlugin()
                    >>> meta = plugin.metadata
                    >>> print(f"Plugin: {meta.name} v{meta.version}")
                    Plugin: lineage v0.1.0
                    >>> print(meta.description)
                    Lineage CLI commands

        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Lineage CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

                Returns the lineage command group which contains all lineage-related
        subcommands registered under the 'phlo lineage' namespace.

        Returns:
                    List containing the root lineage command group (click.Group).
                    The group includes subcommands: show, export, impact, status, and column.

                Command Group Structure:
                    lineage (Group)
                    ├── show (Command)
                    ├── export (Command)
                    ├── impact (Command)
                    ├── status (Command)
                    └── column (Group)
                        ├── import-dbt (Command)
                        ├── upstream (Command)
                        └── downstream (Command)

                Registration:
                    The CLI framework calls this method during plugin discovery and
                    adds returned commands to the main phlo CLI hierarchy.

        Example:
                    >>> plugin = LineageCliPlugin()
                    >>> commands = plugin.get_cli_commands()
                    >>> print(f"Registered {len(commands)} command group(s)")
                    1
                    >>> cmd = commands[0]
                    >>> print(f"Group name: {cmd.name}")
                    Group name: lineage
                    >>> print(f"Subcommands: {[c.name for c in cmd.commands.values()]}")
                    Subcommands: ['show', 'export', 'impact', 'status', 'column']

        See Also:
                    phlo_lineage.cli_lineage.lineage_group for the command implementation.
                    click.Group for command group behavior.

        """
        return [lineage_group]
