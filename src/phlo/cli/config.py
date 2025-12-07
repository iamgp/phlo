"""
Configuration Management Commands

Commands for managing phlo.yaml infrastructure configuration.
"""

import sys
from pathlib import Path

import click
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from phlo.config_schema import InfrastructureConfig, get_default_infrastructure_config
from phlo.infrastructure import clear_config_cache, load_infrastructure_config

console = Console()


@click.group()
def config():
    """Manage infrastructure configuration."""
    pass


@config.command("show")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
def show(format: str):
    """Show the effective infrastructure configuration.

    \b
    Examples:
      phlo config show
      phlo config show --format json
    """
    infra_config = load_infrastructure_config()

    if format == "yaml":
        config_dict = infra_config.model_dump(exclude_none=False)
        yaml_output = yaml.dump(
            {"infrastructure": config_dict},
            default_flow_style=False,
            sort_keys=False,
        )
        syntax = Syntax(yaml_output, "yaml", theme="monokai", line_numbers=False)
        console.print("\n[bold]Effective Infrastructure Configuration:[/bold]\n")
        console.print(syntax)
    else:
        config_dict = infra_config.model_dump(exclude_none=False)
        console.print_json(data={"infrastructure": config_dict})


@config.command("validate")
def validate():
    """Validate infrastructure configuration in phlo.yaml.

    \b
    Examples:
      phlo config validate
    """
    config_path = Path.cwd() / "phlo.yaml"

    if not config_path.exists():
        console.print("[yellow]Warning: No phlo.yaml found in current directory[/yellow]")
        console.print("Run [cyan]phlo services init[/cyan] to create infrastructure configuration")
        sys.exit(1)

    console.print(f"Validating: {config_path}\n")

    with open(config_path) as f:
        project_config = yaml.safe_load(f)

    if not project_config:
        console.print("[red]Error: phlo.yaml is empty[/red]", err=True)
        sys.exit(1)

    if "infrastructure" not in project_config:
        console.print("[yellow]Warning: No infrastructure section in phlo.yaml[/yellow]")
        console.print(
            "Using default configuration. Run [cyan]phlo config upgrade[/cyan] to add infrastructure section."
        )
        return

    try:
        infra_data = project_config["infrastructure"]
        infra_config = InfrastructureConfig(**infra_data)
    except ValidationError as e:
        console.print("[red]Validation Error:[/red]\n", err=True)
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            console.print(f"  [red]•[/red] {loc}: {error['msg']}", err=True)
        console.print(
            "\n[yellow]Fix these errors in phlo.yaml and run validate again.[/yellow]",
            err=True,
        )
        sys.exit(1)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    table.add_row("Schema Validation", "✓ Valid", "All fields conform to schema")
    table.add_row(
        "Services Defined",
        "✓ Valid",
        f"{len(infra_config.services)} services configured",
    )
    table.add_row(
        "Naming Pattern",
        "✓ Valid",
        f"Pattern: {infra_config.container_naming_pattern}",
    )
    table.add_row(
        "Network Config",
        "✓ Valid",
        f"Driver: {infra_config.network.driver}",
    )

    console.print(table)
    console.print("\n[green]✓ Configuration is valid![/green]\n")


@config.command("upgrade")
@click.option("--force", is_flag=True, help="Overwrite existing infrastructure section")
def upgrade(force: bool):
    """Add infrastructure section to existing phlo.yaml.

    \b
    Examples:
      phlo config upgrade
      phlo config upgrade --force
    """
    config_path = Path.cwd() / "phlo.yaml"

    if not config_path.exists():
        console.print("[red]Error: No phlo.yaml found in current directory[/red]", err=True)
        console.print(
            "Run [cyan]phlo services init[/cyan] to create a new project",
            err=True,
        )
        sys.exit(1)

    with open(config_path) as f:
        project_config = yaml.safe_load(f) or {}

    if "infrastructure" in project_config and not force:
        console.print("[yellow]Infrastructure section already exists in phlo.yaml[/yellow]")
        console.print("Use --force to overwrite", err=True)
        sys.exit(1)

    default_infra = get_default_infrastructure_config()
    project_config["infrastructure"] = default_infra.model_dump(exclude_none=False, mode="python")

    with open(config_path, "w") as f:
        yaml.dump(
            project_config,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    console.print(f"[green]✓ Updated {config_path}[/green]")
    console.print(f"Added infrastructure section with {len(default_infra.services)} services\n")

    clear_config_cache()

    console.print("Next steps:")
    console.print("  1. Review the infrastructure section in phlo.yaml")
    console.print("  2. Run [cyan]phlo config validate[/cyan] to verify")
    console.print("  3. Customize service names or container patterns if needed")
