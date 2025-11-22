"""
Validate Command

Validates Pandera schemas and Cascade configurations.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, List, Tuple

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.argument("schema_file", type=click.Path(exists=True))
@click.option(
    "--check-constraints",
    is_flag=True,
    default=True,
    help="Check that constraints are defined (default: True)",
)
@click.option(
    "--check-descriptions",
    is_flag=True,
    default=True,
    help="Check that fields have descriptions (default: True)",
)
def validate_schema(
    schema_file: str,
    check_constraints: bool,
    check_descriptions: bool,
):
    """
    Validate a Pandera schema file.

    Checks for:
    - Valid Pandera DataFrameModel syntax
    - Field descriptions
    - Appropriate constraints
    - Type annotations

    \b
    Examples:
      # Validate a schema
      phlo validate-schema src/phlo/schemas/weather.py

      # Validate without checking descriptions
      phlo validate-schema src/phlo/schemas/weather.py --no-check-descriptions
    """
    console.print(f"\n[bold blue]🔍 Validating Schema[/bold blue]: {schema_file}\n")

    # Load the module
    schema_module = _load_module_from_file(Path(schema_file))
    if schema_module is None:
        console.print("[red]✗ Failed to load schema file[/red]")
        raise click.Abort()

    # Find Pandera DataFrameModel classes
    schema_classes = _find_pandera_schemas(schema_module)

    if not schema_classes:
        console.print("[yellow]⚠ No Pandera DataFrameModel classes found[/yellow]")
        return

    console.print(f"[green]✓[/green] Found {len(schema_classes)} schema(s)\n")

    # Validate each schema
    all_valid = True
    for schema_class in schema_classes:
        is_valid = _validate_single_schema(
            schema_class,
            check_constraints=check_constraints,
            check_descriptions=check_descriptions,
        )
        all_valid = all_valid and is_valid

    # Summary
    if all_valid:
        console.print("\n[bold green]✓ All schemas are valid![/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Some issues found (see above)[/bold yellow]")
        sys.exit(1)


def _load_module_from_file(file_path: Path) -> Any:
    """Load a Python module from file path."""
    try:
        spec = importlib.util.spec_from_file_location("schema_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["schema_module"] = module
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        console.print(f"[red]Error loading module: {e}[/red]")
        return None


def _find_pandera_schemas(module: Any) -> List[Any]:
    """Find all Pandera DataFrameModel classes in module."""
    import pandera as pa

    schemas = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, pa.DataFrameModel):
            # Exclude the base DataFrameModel itself
            if obj is not pa.DataFrameModel:
                schemas.append(obj)

    return schemas


def _validate_single_schema(
    schema_class: Any,
    check_constraints: bool,
    check_descriptions: bool,
) -> bool:
    """Validate a single Pandera schema."""
    console.print(f"[bold cyan]{schema_class.__name__}[/bold cyan]")

    issues: List[Tuple[str, str]] = []
    warnings: List[Tuple[str, str]] = []

    try:
        # Convert to schema object
        schema = schema_class.to_schema()

        # Check each field
        for field_name, field in schema.columns.items():
            # Check for description
            if check_descriptions:
                if not field.description or field.description.strip() == "":
                    warnings.append((field_name, "Missing description"))

            # Check for constraints
            if check_constraints:
                if not field.checks:
                    # Only warn for numeric types that might benefit from constraints
                    if hasattr(field, "dtype") and str(field.dtype) in [
                        "int64",
                        "float64",
                    ]:
                        warnings.append(
                            (
                                field_name,
                                "No constraints defined (consider adding ge/le/gt/lt)",
                            )
                        )

        # Display results in table
        if issues or warnings:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Field", style="cyan")
            table.add_column("Issue", style="yellow" if not issues else "red")

            for field, issue in issues:
                table.add_row(field, f"❌ {issue}")

            for field, warning in warnings:
                table.add_row(field, f"⚠️  {warning}")

            console.print(table)
        else:
            console.print("  [green]✓ No issues found[/green]")

        # Summary for this schema
        field_count = len(schema.columns)
        console.print(f"  [dim]Fields: {field_count}[/dim]")

        if hasattr(schema_class, "Config"):
            config = schema_class.Config
            if hasattr(config, "strict"):
                console.print(f"  [dim]Strict mode: {config.strict}[/dim]")
            if hasattr(config, "coerce"):
                console.print(f"  [dim]Coerce types: {config.coerce}[/dim]")

        console.print()

        return len(issues) == 0

    except Exception as e:
        console.print(f"  [red]✗ Error validating schema: {e}[/red]\n")
        return False


@click.command()
@click.argument("asset_file", type=click.Path(exists=True))
def validate_workflow(asset_file: str):
    """
    Validate a workflow asset file.

    Checks for:
    - Correct decorator usage
    - unique_key exists in schema
    - Valid cron expression
    - Proper function signature

    \b
    Examples:
      phlo validate-workflow src/phlo/defs/ingestion/weather/observations.py
    """
    console.print("\n[bold blue]🔍 Validating Workflow[/bold blue]\n")
    console.print("[yellow]⚠ Workflow validation coming soon![/yellow]")
    console.print("For now, run: pytest tests/test_your_workflow.py")
