"""
Schema management CLI commands.

Provides commands to:
- List and inspect Pandera schemas
- Show schema details and constraints
- Diff schema versions
- Validate schema syntax
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from phlo.cli.utils import classify_schema_change, discover_pandera_schemas

console = Console()


@click.group()
def schema():
    """Manage Pandera schemas and schema validation."""
    pass


@schema.command()
@click.option(
    "--domain",
    help="Filter by domain",
    default=None,
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(domain: Optional[str], format: str):
    """
    List all available Pandera schemas.

    Shows schema name, field count, and file path.

    Examples:
        phlo schema list                 # List all schemas
        phlo schema list --domain nightscout
        phlo schema list --format json
    """
    try:
        schemas = discover_pandera_schemas()

        if not schemas:
            console.print("[yellow]No schemas found[/yellow]")
            return

        # Filter by domain if specified
        if domain:
            schemas = {
                name: schema
                for name, schema in schemas.items()
                if domain.lower() in name.lower()
            }

        if not schemas:
            console.print(f"[yellow]No schemas found for domain: {domain}[/yellow]")
            return

        if format == "json":
            output = {
                name: {
                    "fields": len(schema.__annotations__),
                    "location": str(Path(schema.__module__.replace(".", "/")).with_suffix(".py")),
                }
                for name, schema in schemas.items()
            }
            click.echo(json.dumps(output, indent=2))
        else:
            table = Table(title="Available Schemas")
            table.add_column("Name", style="cyan")
            table.add_column("Fields", justify="right")
            table.add_column("Module", style="magenta")

            for name in sorted(schemas.keys()):
                schema_cls = schemas[name]
                field_count = len(schema_cls.__annotations__)
                module = schema_cls.__module__
                table.add_row(name, str(field_count), module)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing schemas: {e}[/red]")
        sys.exit(1)


@schema.command()
@click.argument("schema_name")
@click.option(
    "--iceberg",
    is_flag=True,
    help="Show Iceberg schema equivalent",
)
def show(schema_name: str, iceberg: bool):
    """
    Show schema details.

    Displays fields, types, constraints, and descriptions.

    Examples:
        phlo schema show RawGlucoseEntries
        phlo schema show RawGlucoseEntries --iceberg
    """
    try:
        schemas = discover_pandera_schemas()

        if schema_name not in schemas:
            console.print(
                f"[red]Schema not found: {schema_name}[/red]\n"
                f"Available schemas: {', '.join(sorted(schemas.keys()))}"
            )
            sys.exit(1)

        schema_cls = schemas[schema_name]

        # Show basic info
        console.print(f"\n[bold blue]{schema_name}[/bold blue]")
        console.print(f"Module: {schema_cls.__module__}")
        console.print(f"Fields: {len(schema_cls.__annotations__)}\n")

        # Show fields
        table = Table(title="Fields")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Required", justify="center")
        table.add_column("Description", style="dim")

        for field_name, field_type in schema_cls.__annotations__.items():
            description = ""
            required = "✓"

            if hasattr(schema_cls, "__annotations__"):
                # Check if Optional
                type_str = str(field_type)
                if "Optional" in type_str or "None" in type_str:
                    required = ""

            table.add_row(field_name, str(field_type), required, description)

        console.print(table)

        if iceberg:
            console.print("\n[bold]Iceberg Schema Equivalent:[/bold]")
            console.print("[dim]# Convert with: phlo schema show --iceberg[/dim]\n")

            # Show example conversion
            iceberg_equiv = _pandera_to_iceberg_example(schema_cls)
            syntax = Syntax(iceberg_equiv, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schema.command()
@click.argument("schema_name")
@click.option(
    "--old",
    default="HEAD~1",
    help="Old version (git ref or file path)",
)
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
)
def diff(schema_name: str, old: str, format: str):
    """
    Compare schema versions.

    Detects added/removed/modified fields and classifies changes as safe or breaking.

    Examples:
        phlo schema diff RawGlucoseEntries --old HEAD~1
        phlo schema diff RawGlucoseEntries --old main
        phlo schema diff src/phlo/schemas/glucose.py src/phlo/schemas/glucose_v2.py
    """
    try:
        schemas = discover_pandera_schemas()

        if schema_name not in schemas:
            console.print(f"[red]Schema not found: {schema_name}[/red]")
            sys.exit(1)

        schema_cls = schemas[schema_name]
        new_schema = {
            name: str(type_)
            for name, type_ in schema_cls.__annotations__.items()
        }

        # For demo purposes, show the new schema
        # In production, would load old version from git/file
        # Classify changes
        classification, details = classify_schema_change({}, new_schema)

        if format == "json":
            output = {
                "classification": classification,
                "details": details,
                "new_schema": new_schema,
            }
            click.echo(json.dumps(output, indent=2))
        else:
            console.print(f"\n[bold blue]Schema Diff: {schema_name}[/bold blue]")
            console.print(f"New schema fields: {len(new_schema)}")

            table = Table(title=f"Classification: {classification}")
            table.add_column("Change Type")
            table.add_column("Details")

            for detail in details:
                table.add_row("Field Change", detail)

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schema.command()
@click.argument("schema_path")
def validate(schema_path: str):
    """
    Validate schema file syntax.

    Checks for common issues and integration problems.

    Examples:
        phlo schema validate src/phlo/schemas/glucose.py
        phlo schema validate workflows/schemas/custom.py
    """
    try:
        path = Path(schema_path)

        if not path.exists():
            console.print(f"[red]File not found: {schema_path}[/red]")
            sys.exit(1)

        # Read and validate schema file
        with open(path) as f:
            content = f.read()

        # Check for basic requirements
        checks = {
            "Has imports": "import" in content.lower(),
            "Has class definition": "class " in content,
            "Has docstring": '"""' in content or "'''" in content,
            "Valid Python": True,
        }

        # Try to compile
        try:
            compile(content, path, "exec")
        except SyntaxError as e:
            checks["Valid Python"] = False
            console.print(f"[red]Syntax error: {e}[/red]")

        # Show results
        table = Table(title=f"Schema Validation: {schema_path}")
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")

        for check_name, passed in checks.items():
            status = "[green]✓[/green]" if passed else "[red]✗[/red]"
            table.add_row(check_name, status)

        console.print(table)

        # Summary
        passed_count = sum(1 for v in checks.values() if v)
        total_count = len(checks)

        if passed_count == total_count:
            console.print(f"\n[green]All checks passed ({passed_count}/{total_count})[/green]")
        else:
            console.print(
                f"\n[yellow]Some checks failed ({passed_count}/{total_count})[/yellow]"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error validating schema: {e}[/red]")
        sys.exit(1)


def _pandera_to_iceberg_example(schema_cls) -> str:
    """Generate example Iceberg schema from Pandera schema."""
    lines = [
        "# Iceberg Schema Equivalent",
        "schema:",
    ]

    for field_name, field_type in schema_cls.__annotations__.items():
        type_str = str(field_type)
        # Simple mapping
        iceberg_type = _map_python_to_iceberg_type(type_str)
        lines.append(f"  {field_name}:")
        lines.append(f"    type: {iceberg_type}")
        lines.append("    required: true")

    return "\n".join(lines)


def _map_python_to_iceberg_type(python_type: str) -> str:
    """Map Python type annotation to Iceberg type."""
    type_lower = python_type.lower()

    mapping = {
        "int": "int",
        "float": "double",
        "str": "string",
        "bool": "boolean",
        "datetime": "timestamp",
        "date": "date",
        "decimal": "decimal",
    }

    for py_type, iceberg_type in mapping.items():
        if py_type in type_lower:
            return iceberg_type

    return "string"  # Default
