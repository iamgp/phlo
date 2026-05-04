"""Plugin validation command."""

from __future__ import annotations

import json
import sys

import click

from phlo.cli.commands.plugin.utils import console
from phlo.logging import get_logger
from phlo.plugins import discover_plugins, validate_plugins

logger = get_logger(__name__)


@click.command(name="check")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def check_cmd(output_json: bool):
    """Validate installed plugins.

    Checks that all plugins comply with their interface requirements
    and reports any issues.

    Examples:
        phlo plugin check           # Check all plugins
        phlo plugin check --json    # Output as JSON
    """
    try:
        if not output_json:
            console.print("Validating plugins...")

        # First discover plugins
        discover_plugins(auto_register=True)

        # Then validate
        validation_results = validate_plugins()

        if output_json:
            click.echo(json.dumps(validation_results, indent=2))
            return

        # Rich formatted output
        valid = validation_results.get("valid", [])
        invalid = validation_results.get("invalid", [])
        logger.info(
            "plugin_check_completed",
            valid_count=len(valid),
            invalid_count=len(invalid),
            output_json=output_json,
        )

        console.print(f"\n[green]✓ Valid Plugins: {len(valid)}[/green]")
        if valid:
            for plugin_id in valid:
                console.print(f"  [green]✓[/green] {plugin_id}")

        if invalid:
            logger.warning("plugin_check_validation_failed", invalid_count=len(invalid))
            console.print(f"\n[red]✗ Invalid Plugins: {len(invalid)}[/red]")
            for plugin_id in invalid:
                console.print(f"  [red]✗[/red] {plugin_id}")
            sys.exit(1)
        else:
            console.print("\n[green]All plugins are valid![/green]")

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("plugin_check_failed", output_json=output_json)
        console.print(f"[red]Error validating plugins: {e}[/red]")
        sys.exit(1)
