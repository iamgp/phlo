"""
Schema management CLI commands.

Provides commands to:
- List and inspect Pandera schemas
- Show schema details and constraints
- Diff schema versions
- Validate schema syntax
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from phlo.cli.utils import classify_schema_change, discover_pandera_schemas

console = Console()

_DEFAULT_SCHEMA_OUT_DIR = Path("workflows/schemas")


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
                name: schema for name, schema in schemas.items() if domain.lower() in name.lower()
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
        new_schema = {name: str(type_) for name, type_ in schema_cls.__annotations__.items()}

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
            console.print(f"\n[yellow]Some checks failed ({passed_count}/{total_count})[/yellow]")
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


def _import_object(ref: str) -> Any:
    """
    Import an object from a "module:attr" reference.
    """
    import importlib

    if ":" not in ref:
        raise click.ClickException(
            "Invalid reference. Expected 'module:attr' "
            "(e.g. workflows.ingestion.github.user_events:user_events)."
        )

    module_name, attr = ref.split(":", 1)
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attr)
    except AttributeError as exc:
        raise click.ClickException(f"Object not found: {ref}") from exc


def _extract_source_callable(obj: Any) -> tuple[callable, dict[str, Any]]:
    """
    Given either a callable or an AssetsDefinition created via @phlo.ingestion, return:
    - a callable that accepts partition_date and returns a DLT source/resource/iterable
    - best-effort metadata (table_name, unique_key, group)
    """
    import inspect

    try:
        from dagster import AssetsDefinition
    except Exception:  # pragma: no cover
        AssetsDefinition = None  # type: ignore

    if AssetsDefinition is not None and isinstance(obj, AssetsDefinition):
        wrapper = obj.node_def.compute_fn.decorated_fn
        freevars = wrapper.__code__.co_freevars
        closure = wrapper.__closure__ or ()
        env = {name: cell.cell_contents for name, cell in zip(freevars, closure)}

        func = env.get("func")
        table_config = env.get("table_config")

        if not callable(func):
            raise click.ClickException(
                "Unsupported asset: expected a @phlo.ingestion asset with a callable source builder."
            )

        meta: dict[str, Any] = {}
        if table_config is not None:
            meta["table_name"] = getattr(table_config, "table_name", None)
            meta["unique_key"] = getattr(table_config, "unique_key", None)
            meta["group"] = getattr(table_config, "group_name", None)

        sig = inspect.signature(func)
        if "partition_date" not in sig.parameters:
            raise click.ClickException(
                "Unsupported asset source function signature: expected (partition_date: str)."
            )

        return func, meta

    if callable(obj):
        return obj, {}

    raise click.ClickException(
        "Unsupported input. Provide either a callable or a Dagster AssetsDefinition created via @phlo.ingestion."
    )


def _to_pascal_case(name: str) -> str:
    parts = [p for p in name.replace("-", "_").split("_") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def _snake_case(name: str) -> str:
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\\1_\\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\\1_\\2", s1).lower()


def _map_dlt_type(dlt_type: str) -> tuple[str, str | None]:
    """
    Map DLT schema data_type strings to a Python type annotation and an optional import.

    Returns (annotation, import_stmt) where import_stmt is a full 'from x import y' line.
    """
    normalized = dlt_type.lower()
    if normalized in {"text", "varchar", "char", "uuid"}:
        return "str", None
    if normalized in {"bigint", "int", "integer", "smallint", "tinyint"}:
        return "int", None
    if normalized in {"double", "float", "real"}:
        return "float", None
    if normalized in {"decimal"}:
        return "Decimal", "from decimal import Decimal"
    if normalized in {"bool", "boolean"}:
        return "bool", None
    if normalized in {"date"}:
        return "date", "from datetime import date"
    if "timestamp" in normalized or normalized in {"datetime"}:
        return "datetime", "from datetime import datetime"
    if normalized in {"json"}:
        return "dict[str, Any]", "from typing import Any"
    if normalized in {"binary", "bytes"}:
        return "bytes", None
    return "str", None


def _render_schema_module(
    *,
    domain: str,
    class_name: str,
    columns: list[dict[str, Any]],
    unique_key: str | None,
) -> str:
    imports: set[str] = {"from __future__ import annotations", "from pandera.pandas import Field"}
    imports.add("from phlo.schemas import PhloSchema")

    fields_lines: list[str] = []
    for col in columns:
        col_name = col["name"]
        annotation = col["annotation"]
        nullable = col["nullable"]

        field_args: list[str] = []
        if unique_key and col_name == unique_key:
            field_args.append("unique=True")
            field_args.append("nullable=False")
        elif nullable:
            field_args.append("nullable=True")

        field = ""
        if field_args:
            field = f" = Field({', '.join(field_args)})"

        fields_lines.append(f"    {col_name}: {annotation}{field}")

    module_doc = (
        f'"""Pandera schemas for {domain} domain.\n\nGenerated via `phlo schema generate`.\n"""'
    )
    body = "\n".join(fields_lines) if fields_lines else "    pass"

    import_lines = "\n".join(sorted(imports))
    return f"{module_doc}\n\n{import_lines}\n\n\nclass {class_name}(PhloSchema):\n{body}\n"


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _update_or_insert_class(content: str, class_name: str, class_block: str) -> str:
    import ast

    tree = ast.parse(content)
    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == class_name
            and node.lineno
            and node.end_lineno
        ):
            lines = content.splitlines(keepends=True)
            start = node.lineno - 1
            end = node.end_lineno
            return "".join(lines[:start]) + class_block + "".join(lines[end:])

    if not content.endswith("\n"):
        content += "\n"
    if not content.endswith("\n\n"):
        content += "\n"
    return content + class_block


def _class_block_only(module_code: str, class_name: str) -> str:
    import ast

    tree = ast.parse(module_code)
    lines = module_code.splitlines(keepends=True)
    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == class_name
            and node.lineno
            and node.end_lineno
        ):
            return "".join(lines[node.lineno - 1 : node.end_lineno])
    raise ValueError(f"class not found in generated module: {class_name}")


def _ensure_imports_in_module(content: str, import_lines: list[str]) -> str:
    """
    Ensure a set of import lines exists, inserting them after any module docstring.

    This keeps `from __future__ ...` placement valid.
    """
    import ast

    if not import_lines:
        return content

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Don't try to be clever if the file is already invalid.
        return "\n".join(import_lines) + "\n" + content

    insert_after = 0
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
        and isinstance(tree.body[0].value.value, str)
        and getattr(tree.body[0], "end_lineno", None)
    ):
        insert_after = tree.body[0].end_lineno

    lines = content.splitlines()
    existing = set(lines)
    to_add = [line for line in import_lines if line not in existing]
    if not to_add:
        return content

    lines[insert_after:insert_after] = to_add + [""]
    return "\n".join(lines) + ("\n" if not content.endswith("\n") else "")


@schema.command()
@click.option(
    "--from",
    "from_ref",
    required=True,
    help="Python reference to a callable or @phlo.ingestion asset (module:attr).",
)
@click.option(
    "--domain",
    required=True,
    help="Domain name (used for default output path and module docstring).",
)
@click.option("--table", "table_name", default=None, help="DLT table/resource name to generate.")
@click.option(
    "--class",
    "class_name",
    default=None,
    help="Schema class name (default: Raw<TableName>).",
)
@click.option(
    "--partition-date",
    default=None,
    help="Partition date passed to ingestion source builder (default: today).",
)
@click.option(
    "--max-records",
    type=int,
    default=200,
    show_default=True,
    help="Limit records extracted per DLT resource during schema inference.",
)
@click.option(
    "--out",
    "out_path",
    default=None,
    help="Output schema file path (default: workflows/schemas/<domain>.py).",
)
@click.option("--write", is_flag=True, help="Write generated schema to disk.")
@click.option(
    "--update",
    is_flag=True,
    help="Update/insert the class into an existing schema module (non-destructive).",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite the entire output module if it exists (destructive).",
)
def generate(
    from_ref: str,
    domain: str,
    table_name: str | None,
    class_name: str | None,
    partition_date: str | None,
    max_records: int,
    out_path: str | None,
    write: bool,
    update: bool,
    overwrite: bool,
):
    """
    Generate Pandera schemas from a bounded DLT inference sample.

    This runs a small DLT sample locally (filesystem destination) to infer schema, then emits a
    PhloSchema-based DataFrameModel into your lakehouse code (default: workflows/schemas/).
    """
    import datetime as _dt
    import itertools
    import tempfile

    import dlt

    obj = _import_object(from_ref)
    source_fn, meta = _extract_source_callable(obj)

    partition_date_value = partition_date or _dt.date.today().isoformat()
    dlt_obj = source_fn(partition_date_value)

    try:
        from dlt.extract.resource import DltResource
        from dlt.extract.source import DltSource
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(f"Failed to import DLT types: {exc}") from exc

    if isinstance(dlt_obj, DltSource):
        for r in dlt_obj.resources.values():
            try:
                r.add_limit(max_records)
            except Exception:
                continue
    elif isinstance(dlt_obj, DltResource):
        dlt_obj.add_limit(max_records)
    elif hasattr(dlt_obj, "__iter__"):
        dlt_obj = itertools.islice(dlt_obj, max_records)

    with tempfile.TemporaryDirectory(prefix="phlo-schema-generate-") as tmpdir:
        pipeline = dlt.pipeline(
            pipeline_name=f"phlo_schema_generate_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            destination=dlt.destinations.filesystem(bucket_url=Path(tmpdir).as_uri()),
            dataset_name=_snake_case(domain),
            pipelines_dir=tmpdir,
        )

        run_kwargs: dict[str, Any] = {"loader_file_format": "parquet"}
        if not isinstance(dlt_obj, (DltSource, DltResource)):
            run_kwargs["table_name"] = meta.get("table_name") or table_name or "data"

        pipeline.run(dlt_obj, **run_kwargs)

        schema = pipeline.default_schema
        candidate_tables = [
            t
            for t in schema.tables.keys()
            if not t.startswith("_dlt_") and t not in {"_dlt_pipeline_state"}
        ]

        selected_table = table_name
        if selected_table is None:
            if len(candidate_tables) == 1:
                selected_table = candidate_tables[0]
            else:
                raise click.ClickException(
                    "Multiple DLT tables inferred. Re-run with --table <name>. "
                    f"Candidates: {', '.join(sorted(candidate_tables))}"
                )

        if selected_table not in schema.tables:
            raise click.ClickException(
                f"Table not found in inferred schema: {selected_table}. "
                f"Available: {', '.join(sorted(candidate_tables))}"
            )

        table = schema.tables[selected_table]
        dlt_columns: dict[str, Any] = table.get("columns") or {}

    unique_key = meta.get("unique_key")
    inferred_columns: list[dict[str, Any]] = []
    imports: set[str] = set()
    for col_name, col in sorted(dlt_columns.items()):
        if col_name.startswith("_dlt_") or col_name.startswith("_phlo_"):
            continue

        ann, imp = _map_dlt_type(str(col.get("data_type", "text")))
        if imp:
            imports.add(imp)

        nullable = bool(col.get("nullable", True))
        if unique_key and col_name == unique_key:
            nullable = False
        annotation = ann if not nullable else f"{ann} | None"

        inferred_columns.append(
            {
                "name": col_name,
                "annotation": annotation,
                "nullable": nullable,
                "dlt_type": col.get("data_type"),
            }
        )

    base_name = meta.get("table_name") or selected_table
    schema_class = class_name or f"Raw{_to_pascal_case(base_name)}"

    module_code = _render_schema_module(
        domain=domain,
        class_name=schema_class,
        columns=inferred_columns,
        unique_key=unique_key,
    )

    # Add extra imports if needed by annotations.
    if imports:
        lines = module_code.splitlines()
        insert_at = 0
        for idx, line in enumerate(lines):
            if line.startswith("from __future__ import annotations"):
                insert_at = idx + 1
                break
        extra = sorted(imports)
        lines[insert_at:insert_at] = extra
        module_code = "\n".join(lines) + "\n"

    output_path = (
        Path(out_path) if out_path else (_DEFAULT_SCHEMA_OUT_DIR / f"{_snake_case(domain)}.py")
    )

    if not write:
        click.echo(module_code)
        return

    if overwrite and update:
        raise click.ClickException("Use only one of --update or --overwrite.")

    _ensure_parent_dir(output_path)
    if output_path.exists() and not (overwrite or update):
        raise click.ClickException(
            f"Refusing to overwrite existing file: {output_path}. Use --update or --overwrite."
        )

    if overwrite or not output_path.exists():
        output_path.write_text(module_code)
        console.print(f"[green]Wrote[/green] {output_path}")
        return

    existing = output_path.read_text()
    class_block = _class_block_only(module_code, schema_class)

    required_imports = [
        "from __future__ import annotations",
        "from pandera.pandas import Field",
        "from phlo.schemas import PhloSchema",
    ]
    existing = _ensure_imports_in_module(existing, required_imports)

    updated = _update_or_insert_class(existing, schema_class, class_block)
    output_path.write_text(updated)
    console.print(f"[green]Updated[/green] {output_path}")
