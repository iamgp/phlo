"""Plugin search command."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
from rich.table import Table

from phlo.cli.commands.plugin.utils import (
    INTERNAL_TO_REGISTRY_TYPE,
    console,
    registry_plugin_to_dict,
)
from phlo.plugins.registry_client import search_plugins


@click.command(name="search")
@click.argument("query", required=False)
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(
        [
            "sources",
            "quality",
            "transforms",
            "services",
            "hooks",
            "assets",
            "resources",
            "orchestrators",
            "catalogs",
        ]
    ),
    help="Filter by plugin type",
)
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Filter by one or more tags",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def search_cmd(
    query: Optional[str], plugin_type: Optional[str], tags: tuple[str, ...], output_json: bool
):
    """Search plugin registry."""
    try:
        if plugin_type:
            plugin_type = INTERNAL_TO_REGISTRY_TYPE.get(plugin_type, plugin_type)
        results = search_plugins(
            query=query,
            plugin_type=plugin_type,
            tags=list(tags) if tags else None,
        )

        output = [registry_plugin_to_dict(plugin) for plugin in results]

        if output_json:
            console.print(json.dumps(output, indent=2))
            return

        if not output:
            console.print("No plugins found.")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Package", style="white")
        table.add_column("Verified", style="blue")

        for plugin in output:
            table.add_row(
                plugin["name"],
                plugin["type"],
                plugin["version"],
                plugin["package"],
                "yes" if plugin["verified"] else "no",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error searching registry: {e}[/red]")
        sys.exit(1)
