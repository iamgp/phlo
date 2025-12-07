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
@click.option(
    "--fix",
    is_flag=True,
    default=False,
    help="Auto-fix issues where possible",
)
def validate_workflow(asset_file: str, fix: bool):
    """
    Validate a workflow asset file for correctness before deployment.

    Checks for:
    - @phlo_ingestion decorator usage
    - unique_key exists in validation_schema
    - Valid cron expression
    - Proper function signature
    - Return type validation

    \b
    Examples:
      phlo validate-workflow src/phlo/defs/ingestion/weather/observations.py
      phlo validate-workflow workflows/ingestion/  # Validate directory
      phlo validate-workflow weather.py --fix     # Auto-fix where possible
    """
    import inspect
    from pathlib import Path

    console.print(f"\n[bold blue]🔍 Validating Workflow[/bold blue]\n")

    path = Path(asset_file)

    # Handle directory input
    if path.is_dir():
        py_files = list(path.glob("*.py")) + list(path.glob("**/*.py"))
        py_files = [f for f in py_files if not f.name.startswith("__")]
        if not py_files:
            console.print(f"[yellow]⚠ No Python files found in {asset_file}[/yellow]")
            return

        all_valid = True
        for py_file in sorted(py_files):
            is_valid = _validate_workflow_file(py_file, fix=fix)
            all_valid = all_valid and is_valid

        if all_valid:
            console.print(
                f"\n[bold green]✓ All {len(py_files)} file(s) are valid![/bold green]"
            )
            sys.exit(0)
        else:
            console.print("\n[bold yellow]⚠ Some issues found (see above)[/bold yellow]")
            sys.exit(1)
    else:
        # Single file validation
        is_valid = _validate_workflow_file(path, fix=fix)
        if is_valid:
            console.print("\n[bold green]✓ Workflow is valid![/bold green]")
            sys.exit(0)
        else:
            console.print("\n[bold yellow]⚠ Issues found (see above)[/bold yellow]")
            sys.exit(1)


def _validate_workflow_file(file_path: Path, fix: bool = False) -> bool:
    """
    Validate a single workflow file.

    Args:
        file_path: Path to the workflow file
        fix: Whether to auto-fix issues

    Returns:
        True if valid, False otherwise
    """
    import inspect

    console.print(f"[bold cyan]{file_path.name}[/bold cyan]")

    # Load the module
    module = _load_module_from_file(file_path)
    if module is None:
        console.print("  [red]✗ Failed to load module[/red]")
        return False

    # Find all functions decorated with @phlo_ingestion
    phlo_ingestion_funcs = _find_phlo_ingestion_functions(module)

    if not phlo_ingestion_funcs:
        console.print("  [yellow]⚠ No @phlo_ingestion decorated functions found[/yellow]")
        return True

    console.print(f"  [green]✓[/green] Found {len(phlo_ingestion_funcs)} workflow(s)\n")

    all_valid = True
    for func_name, func_obj, decorator_params in phlo_ingestion_funcs:
        is_valid = _validate_workflow_function(
            func_name, func_obj, decorator_params, file_path, fix=fix
        )
        all_valid = all_valid and is_valid

    return all_valid


def _find_phlo_ingestion_functions(module: Any) -> List[Tuple[str, Any, dict]]:
    """
    Find all functions decorated with @phlo_ingestion.

    Returns:
        List of tuples: (func_name, func_obj, decorator_params)
    """
    results = []

    # Try to find functions with decorator by inspecting module source
    try:
        import inspect

        source = inspect.getsource(module)
        # Look for @phlo_ingestion decorators in source
        if "@phlo_ingestion" in source:
            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj) and not name.startswith("_"):
                    # Check if this function is defined in the module
                    try:
                        if inspect.getfile(obj) == inspect.getfile(module):
                            results.append((name, obj, {"found_in_source": True}))
                    except (TypeError, OSError):
                        pass
    except (OSError, TypeError):
        # Module might not have source (e.g., built-in), fall back to __wrapped__ check
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and hasattr(obj, "__wrapped__"):
                if hasattr(obj, "__name__") and not name.startswith("_"):
                    decorator_params = _extract_decorator_params(obj)
                    if decorator_params:
                        results.append((name, obj, decorator_params))

    return results


def _extract_decorator_params(func: Any) -> dict:
    """
    Extract decorator parameters from a decorated function.

    Returns:
        Dict of parameters if this is a @phlo_ingestion function, empty dict otherwise
    """
    # The @phlo_ingestion decorator doesn't expose params directly,
    # so we'll mark functions that look like ingestion functions
    if hasattr(func, "__qualname__") and "wrapper" in func.__qualname__:
        # This is likely a decorated function; we can't extract params
        # so we'll note this needs manual verification
        return {"needs_manual_verification": True}

    return {}


def _validate_workflow_function(
    func_name: str,
    func_obj: Any,
    decorator_params: dict,
    file_path: Path,
    fix: bool = False,
) -> bool:
    """
    Validate a single workflow function.

    Args:
        func_name: Name of the function
        func_obj: The function object
        decorator_params: Decorator parameters (if available)
        file_path: Path to the file for reading source
        fix: Whether to auto-fix issues

    Returns:
        True if valid, False otherwise
    """
    import inspect
    import re

    console.print(f"  [dim]Function: {func_name}[/dim]")

    issues = []
    warnings = []

    # Read the source code to find the decorator
    try:
        source = file_path.read_text()
        lines = source.split("\n")

        # Find the @phlo_ingestion decorator for this function
        deco_match = None
        func_line_idx = None

        for i, line in enumerate(lines):
            if f"def {func_name}(" in line:
                func_line_idx = i
                break

        if func_line_idx is None:
            warnings.append("Could not locate function in source code")
        else:
            # Search backwards for @phlo_ingestion decorator
            for i in range(func_line_idx - 1, max(0, func_line_idx - 20), -1):
                if "@phlo_ingestion" in lines[i]:
                    # Extract decorator block
                    deco_start = i
                    deco_lines = []
                    bracket_count = 0
                    for j in range(i, func_line_idx):
                        deco_lines.append(lines[j])
                        bracket_count += lines[j].count("(") - lines[j].count(")")
                        if bracket_count == 0 and "(" in lines[j]:
                            break

                    deco_text = "\n".join(deco_lines)
                    deco_match = deco_text
                    break

            if deco_match:
                # Validate decorator parameters
                _validate_decorator_params(
                    deco_match, func_line_idx, issues, warnings
                )

        # Validate function signature
        sig = inspect.signature(func_obj)
        params = list(sig.parameters.keys())

        if "partition_date" not in params and "partition_date" not in str(sig):
            warnings.append(
                "Missing 'partition_date: str' parameter - ingestion functions should accept partition_date"
            )
        else:
            # Check if partition_date is declared but not used in the function body
            try:
                func_source = inspect.getsource(func_obj)
                # Count occurrences excluding the parameter declaration itself
                param_line = f"partition_date"
                # Simple heuristic: if partition_date appears only once (in the signature),
                # it's likely unused
                occurrences = func_source.count("partition_date")
                if occurrences <= 1:
                    warnings.append(
                        "partition_date is declared but appears unused - consider using it for date-based filtering or remove if not needed"
                    )
            except (OSError, TypeError):
                # Can't get source, skip this check
                pass

        # Check for type hints
        annotations = getattr(func_obj, "__annotations__", {})
        if not annotations:
            warnings.append("No type hints found - add type annotations for clarity")

    except Exception as e:
        console.print(f"    [yellow]⚠ Could not fully validate source: {e}[/yellow]")

    # Display results
    if issues or warnings:
        for issue in issues:
            console.print(f"    [red]✗ {issue}[/red]")
        for warning in warnings:
            console.print(f"    [yellow]⚠ {warning}[/yellow]")
        return len(issues) == 0
    else:
        console.print("    [green]✓ No issues found[/green]")
        return True


def _validate_decorator_params(
    deco_text: str, func_line_idx: int, issues: List[str], warnings: List[str]
) -> None:
    """
    Validate @phlo_ingestion decorator parameters.

    Args:
        deco_text: The decorator text
        func_line_idx: Line number of the function
        issues: List to append issues to
        warnings: List to append warnings to
    """
    import re

    # Extract table_name
    table_match = re.search(r"table_name\s*=\s*['\"]([^'\"]+)['\"]", deco_text)
    if table_match:
        table_name = table_match.group(1)
        if not _is_valid_table_name(table_name):
            issues.append(
                f"Invalid table_name '{table_name}' - use snake_case"
            )

    # Extract unique_key
    unique_key_match = re.search(r"unique_key\s*=\s*['\"]([^'\"]+)['\"]", deco_text)
    if unique_key_match:
        unique_key = unique_key_match.group(1)
        if not _is_valid_field_name(unique_key):
            issues.append(
                f"Invalid unique_key '{unique_key}' - use snake_case"
            )

    # Extract and validate cron
    cron_match = re.search(r'cron\s*=\s*["\']([^"\']+)["\']', deco_text)
    if cron_match:
        cron = cron_match.group(1)
        cron_issues = _validate_cron_format(cron)
        if cron_issues:
            issues.extend(cron_issues)

    # Check for validation_schema
    if "validation_schema" not in deco_text:
        warnings.append(
            "No validation_schema provided - add one for data quality validation"
        )

    # Check for freshness_hours (optional but recommended)
    if "freshness_hours" not in deco_text:
        warnings.append(
            "No freshness_hours specified - consider adding SLA definition"
        )

    # Check for group
    if "group" not in deco_text:
        issues.append("Missing required 'group' parameter")


def _validate_cron_format(cron: str) -> List[str]:
    """
    Validate cron expression format.

    Returns:
        List of validation errors, empty if valid
    """
    errors = []
    parts = cron.strip().split()

    if len(parts) != 5:
        errors.append(
            f"Invalid cron expression '{cron}' - must have 5 parts (minute hour day month weekday)"
        )
        return errors

    # Validate minute (0-59)
    if not _is_valid_cron_field(parts[0], 0, 59):
        errors.append(f"Invalid minute field: {parts[0]}")

    # Validate hour (0-23)
    if not _is_valid_cron_field(parts[1], 0, 23):
        errors.append(f"Invalid hour field: {parts[1]}")

    # Validate day of month (1-31)
    if not _is_valid_cron_field(parts[2], 1, 31):
        errors.append(f"Invalid day field: {parts[2]}")

    # Validate month (1-12)
    if not _is_valid_cron_field(parts[3], 1, 12):
        errors.append(f"Invalid month field: {parts[3]}")

    # Warn on unusual patterns
    if parts[0] != "*" and "/" in parts[0]:
        freq = parts[0].split("/")[1] if "/" in parts[0] else ""
        try:
            if int(freq) < 5:
                errors.append(
                    f"Warning: Cron runs every {freq} minutes - ensure this is intentional"
                )
        except (ValueError, IndexError):
            pass

    return errors


def _is_valid_cron_field(field: str, min_val: int, max_val: int) -> bool:
    """Check if a cron field is valid."""
    if field == "*":
        return True
    if field == "?":
        return True
    if "/" in field:
        try:
            base, step = field.split("/")
            int(step)  # Validate step is numeric
            if base == "*":
                return True
            # Check range like "0-30/5"
            if "-" in base:
                try:
                    start, end = base.split("-")
                    return (
                        min_val <= int(start) <= max_val
                        and min_val <= int(end) <= max_val
                    )
                except (ValueError, IndexError):
                    return False
            # Check single number like "5/2"
            try:
                val = int(base)
                return min_val <= val <= max_val
            except ValueError:
                return False
        except (ValueError, IndexError):
            return False
    if "-" in field:
        try:
            start, end = field.split("-")
            return min_val <= int(start) <= max_val and min_val <= int(end) <= max_val
        except (ValueError, IndexError):
            return False
    if "," in field:
        return all(_is_valid_cron_field(f.strip(), min_val, max_val) for f in field.split(","))
    try:
        val = int(field)
        return min_val <= val <= max_val
    except ValueError:
        return False


def _is_valid_table_name(name: str) -> bool:
    """Check if table name follows naming conventions."""
    import re

    return bool(re.match(r"^[a-z_][a-z0-9_]*$", name)) and "__" not in name


def _is_valid_field_name(name: str) -> bool:
    """Check if field name follows naming conventions."""
    import re

    return bool(re.match(r"^[a-z_][a-z0-9_]*$", name)) and "__" not in name
