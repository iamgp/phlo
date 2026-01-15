"""Plugin install command."""

from __future__ import annotations

import sys

import click

from phlo.cli.commands.plugin.utils import console, run_pip
from phlo.plugins.registry_client import get_plugin as get_registry_plugin


def resolve_install_target(plugin_name: str) -> tuple[str, str]:
    """Resolve plugin name to package spec and display name."""
    if "==" in plugin_name:
        name_part, version_part = plugin_name.split("==", 1)
    else:
        name_part, version_part = plugin_name, None

    registry_plugin = get_registry_plugin(name_part)
    if registry_plugin:
        version = version_part or registry_plugin.version
        package_spec = f"{registry_plugin.package}=={version}"
        display_name = f"{registry_plugin.name} ({registry_plugin.package})"
        return package_spec, display_name

    return plugin_name, plugin_name


@click.command(name="install")
@click.argument("plugin_name")
def install_cmd(plugin_name: str):
    """Install a plugin from the registry (wraps pip)."""
    try:
        package_spec, display_name = resolve_install_target(plugin_name)
        console.print(f"Installing {display_name}...")
        run_pip(["install", package_spec])
        console.print(f"[green]✓ Installed {display_name}[/green]")
    except Exception as e:
        console.print(f"[red]Error installing plugin: {e}[/red]")
        sys.exit(1)
