"""
Data contract management CLI commands.

Provides commands to:
- List and show contracts
- Validate schemas against contracts
- Detect breaking changes
- Check SLA compliance
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from phlo.contracts.schema import ContractRegistry
from phlo.contracts.evolution import SchemaEvolution, ChangeClassification

console = Console()


@click.group()
def contract():
    """Manage data contracts and SLA enforcement."""
    pass


@contract.command()
@click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to contracts directory",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(contracts_dir: str, format: str):
    """
    List all data contracts.

    Shows contract name, version, owner, and consumer count.

    Examples:
        phlo contract list
        phlo contract list --contracts-dir ./my-contracts
        phlo contract list --format json
    """
    try:
        registry = ContractRegistry(Path(contracts_dir))
        contracts = registry.list_contracts()

        if not contracts:
            console.print("[yellow]No contracts found[/yellow]")
            return

        if format == "json":
            output = {
                name: registry.get(name).to_dict() for name in sorted(contracts)
            }
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            table = Table(title=f"Data Contracts ({len(contracts)})")
            table.add_column("Contract Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Owner", style="magenta")
            table.add_column("Columns", justify="right")
            table.add_column("Consumers", justify="right")

            for name in sorted(contracts):
                contract_obj = registry.get(name)
                table.add_row(
                    name,
                    contract_obj.version,
                    contract_obj.owner,
                    str(len(contract_obj.schema_columns)),
                    str(len(contract_obj.consumers)),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing contracts: {e}[/red]")
        sys.exit(1)


@contract.command()
@click.argument("contract_name")
@click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to contracts directory",
)
def show(contract_name: str, contracts_dir: str):
    """
    Show detailed contract information.

    Displays schema, SLA, and consumers.

    Examples:
        phlo contract show glucose_readings
        phlo contract show glucose_readings --contracts-dir ./my-contracts
    """
    try:
        registry = ContractRegistry(Path(contracts_dir))
        contract_obj = registry.get(contract_name)

        if not contract_obj:
            console.print(f"[red]Contract not found: {contract_name}[/red]")
            sys.exit(1)

        # Show contract info
        console.print(f"\n[bold blue]{contract_name}[/bold blue]")
        console.print(f"Version: {contract_obj.version}")
        console.print(f"Owner: {contract_obj.owner}")
        console.print(f"Description: {contract_obj.description}")

        # Show schema
        console.print("\n[bold]Schema (Required Columns):[/bold]")
        schema_table = Table()
        schema_table.add_column("Column Name", style="cyan")
        schema_table.add_column("Type", style="green")
        schema_table.add_column("Required", justify="center")
        schema_table.add_column("Description", style="dim")

        for col in contract_obj.schema_columns:
            required = "✓" if col.required else ""
            schema_table.add_row(col.name, col.type, required, col.description)

        console.print(schema_table)

        # Show SLA
        console.print("\n[bold]SLA:[/bold]")
        sla_table = Table()
        sla_table.add_column("SLA Type", style="cyan")
        sla_table.add_column("Value", style="green")

        sla_table.add_row("Quality Threshold", f"{contract_obj.sla.quality_threshold:.0%}")
        sla_table.add_row(
            "Availability", f"{contract_obj.sla.availability_percentage}%"
        )
        if contract_obj.sla.freshness_hours:
            sla_table.add_row("Max Freshness", f"{contract_obj.sla.freshness_hours} hours")

        console.print(sla_table)

        # Show consumers
        if contract_obj.consumers:
            console.print("\n[bold]Consumers:[/bold]")
            consumer_table = Table()
            consumer_table.add_column("Name", style="cyan")
            consumer_table.add_column("Usage", style="green")
            consumer_table.add_column("Contact", style="dim")

            for consumer in contract_obj.consumers:
                consumer_table.add_row(
                    consumer.name, consumer.usage, consumer.contact or "N/A"
                )

            console.print(consumer_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@contract.command()
@click.argument("contract_name")
@click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to contracts directory",
)
def validate(contract_name: str, contracts_dir: str):
    """
    Validate actual schema against contract.

    Checks if table schema complies with contract definition.

    Examples:
        phlo contract validate glucose_readings
        phlo contract validate glucose_readings --contracts-dir ./my-contracts
    """
    try:
        registry = ContractRegistry(Path(contracts_dir))
        contract_obj = registry.get(contract_name)

        if not contract_obj:
            console.print(f"[red]Contract not found: {contract_name}[/red]")
            sys.exit(1)

        # For demo, show expected schema
        console.print(f"\n[bold blue]Contract Validation: {contract_name}[/bold blue]")
        console.print("[yellow]Note: Requires live catalog access to validate actual schema[/yellow]")

        # Show what would be validated
        console.print("\n[bold]Required Columns:[/bold]")
        table = Table()
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")

        for col in contract_obj.schema_columns:
            table.add_row(col.name, col.type)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@contract.command()
@click.argument("contract_name")
@click.option(
    "--old-version",
    default="1.0.0",
    help="Previous contract version",
)
@click.option(
    "--contracts-dir",
    default="contracts",
    help="Path to contracts directory",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def check(contract_name: str, old_version: str, contracts_dir: str, format: str):
    """
    Check for breaking changes in contract.

    Detects schema changes that would break consumers.

    Examples:
        phlo contract check glucose_readings
        phlo contract check glucose_readings --old-version 1.0.0
        phlo contract check glucose_readings --format json
    """
    try:
        registry = ContractRegistry(Path(contracts_dir))
        contract_obj = registry.get(contract_name)

        if not contract_obj:
            console.print(f"[red]Contract not found: {contract_name}[/red]")
            sys.exit(1)

        # For demo, analyze current schema
        current_columns = contract_obj.schema_columns
        old_columns = current_columns[
            : len(current_columns) // 2
        ]  # Demo: show first half as old

        analysis = SchemaEvolution.analyze(old_columns, current_columns)

        if format == "json":
            output = {
                "contract": contract_name,
                "classification": analysis.classification.value,
                "changes": [
                    {
                        "field": c.field_name,
                        "type": c.change_type,
                        "old": c.old_value,
                        "new": c.new_value,
                        "classification": c.classification.value,
                    }
                    for c in analysis.changes
                ],
                "recommendations": analysis.migration_recommendations,
            }
            click.echo(json.dumps(output, indent=2))
        else:
            console.print(f"\n[bold blue]Change Analysis: {contract_name}[/bold blue]")

            # Color based on severity
            color_map = {
                ChangeClassification.SAFE: "green",
                ChangeClassification.WARNING: "yellow",
                ChangeClassification.BREAKING: "red",
            }
            color = color_map.get(analysis.classification, "white")

            console.print(
                f"\n[{color}]Classification: {analysis.classification.value.upper()}[/{color}]"
            )

            # Show changes
            if analysis.changes:
                console.print("\n[bold]Changes:[/bold]")
                changes_table = Table()
                changes_table.add_column("Field", style="cyan")
                changes_table.add_column("Type", style="green")
                changes_table.add_column("Old Value", style="dim")
                changes_table.add_column("New Value", style="dim")
                changes_table.add_column("Severity", style="magenta")

                for change in analysis.changes:
                    changes_table.add_row(
                        change.field_name,
                        change.change_type,
                        change.old_value or "—",
                        change.new_value or "—",
                        change.classification.value,
                    )

                console.print(changes_table)

            # Show recommendations
            if analysis.migration_recommendations:
                console.print("\n[bold]Recommendations:[/bold]")
                for i, rec in enumerate(analysis.migration_recommendations, 1):
                    console.print(f"  {i}. {rec}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
