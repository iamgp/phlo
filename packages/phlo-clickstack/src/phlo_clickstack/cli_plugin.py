"""CLI plugin for ClickStack commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_clickstack.cli import clickstack_group


class ClickStackCliPlugin(CliCommandPlugin):
    """Register ClickStack CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for ClickStack CLI registration."""
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="CLI commands for ClickStack query access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return ClickStack CLI commands."""
        return [clickstack_group]
