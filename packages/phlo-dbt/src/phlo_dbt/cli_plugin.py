"""CLI plugin for dbt-related commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dbt.cli_publishing import publishing


class DbtCliPlugin(CliCommandPlugin):
    """CLI plugin exposing dbt-related commands."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt CLI plugin.
        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            List of click commands to register.
        """
        return [publishing]
