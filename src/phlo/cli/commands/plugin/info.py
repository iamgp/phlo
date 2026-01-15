"""Plugin info command."""

from __future__ import annotations

import json
import sys

import click

from phlo.cli.commands.plugin.utils import PLUGIN_TYPE_CHOICES, PLUGIN_TYPE_MAP, console
from phlo.plugins import get_plugin_info, list_plugins


@click.command(name="info")
@click.argument("plugin_name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(PLUGIN_TYPE_CHOICES),
    help="Plugin type (auto-detected if not specified)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def info_cmd(plugin_name: str, plugin_type: str | None, output_json: bool):
    """Show detailed plugin information.

    Examples:
        phlo plugin info github              # Show info for 'github' plugin
        phlo plugin info custom --type quality
        phlo plugin info github --json
    """
    try:
        all_plugins = list_plugins()

        plugin_type_provided = bool(plugin_type)
        detected_type = None

        if not plugin_type_provided:
            for ptype_key, names in all_plugins.items():
                if plugin_name in names:
                    detected_type = ptype_key
                    break

            if not detected_type:
                console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
                sys.exit(1)

        internal_type = (
            PLUGIN_TYPE_MAP[plugin_type]
            if plugin_type_provided
            else detected_type
        )

        info = get_plugin_info(internal_type, plugin_name)

        if not info:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)

        if output_json:
            console.print(json.dumps(info, indent=2))
            return

        # Rich formatted output
        console.print(f"\n[bold cyan]{info['name']}[/bold cyan]")
        console.print(f"Type: {plugin_type}")
        console.print(f"Version: {info['version']}")

        if info.get("author"):
            console.print(f"Author: {info['author']}")

        if info.get("description"):
            console.print(f"Description: {info['description']}")

        if info.get("license"):
            console.print(f"License: {info['license']}")

        if info.get("homepage"):
            console.print(f"Homepage: {info['homepage']}")

        if info.get("tags"):
            console.print(f"Tags: {', '.join(info['tags'])}")

        if info.get("dependencies"):
            console.print("Dependencies:")
            for dep in info["dependencies"]:
                console.print(f"  - {dep}")

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error getting plugin info: {e}[/red]")
        sys.exit(1)
