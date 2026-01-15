"""Plugin update command."""

from __future__ import annotations

import json
import sys

import click

from phlo.cli.commands.plugin.utils import console, find_available_updates, run_pip
from phlo.plugins.registry_client import list_registry_plugins


@click.command(name="update")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def update_cmd(output_json: bool):
    """Update installed plugins based on registry versions."""
    try:
        registry_plugins = list_registry_plugins()
        updates = find_available_updates(registry_plugins)

        if output_json:
            console.print(json.dumps(updates, indent=2))
            return

        if not updates:
            console.print("No plugin updates available.")
            return

        console.print("Updates available:")
        for update in updates:
            console.print(
                f"  {update['name']}: {update['installed_version']} → {update['available_version']}"
            )

        for update in updates:
            run_pip(["install", "--upgrade", f"{update['package']}=={update['available_version']}"])

        console.print("[green]✓ Plugins updated[/green]")
    except Exception as e:
        console.print(f"[red]Error updating plugins: {e}[/red]")
        sys.exit(1)
