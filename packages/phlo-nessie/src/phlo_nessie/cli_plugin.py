"""CLI plugin for Nessie commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_nessie.cli_branch import branch
from phlo_nessie.cli_catalog import catalog


class NessieCliPlugin(CliCommandPlugin):
    """Register Nessie CLI commands with the Phlo plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for Nessie CLI integration.

        Returns:
            PluginMetadata: Plugin identity, version, and description.
        """
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Nessie catalog and branch management commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered Nessie command groups.
        """
        return [catalog, branch]
