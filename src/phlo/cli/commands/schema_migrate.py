"""Schema migration CLI commands.

Provides commands to diff, plan, apply, and inspect schema migrations
between quality provider schemas and storage tables.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from phlo.logging import get_logger

console = Console()
logger = get_logger(__name__)


def _resolve_migrator() -> Any:
    """Resolve the registered SchemaMigrator from the capability registry."""
    from phlo.capabilities import get_capability_registry

    registry = get_capability_registry()
    migrators = registry.list_schema_migrators()
    if not migrators:
        console.print("[red]No schema migrator registered.[/red]")
        console.print("Install a storage provider (e.g. phlo-iceberg) that implements SchemaMigrator.")
        sys.exit(1)
    return migrators[0].provider


def _resolve_extractor() -> Any:
    """Resolve a SchemaExtractor by attempting known quality providers."""
    try:
        from phlo_quality.schema_extractor import PanderaSchemaExtractor

        return PanderaSchemaExtractor()
    except ImportError:
        return None


def _discover_schema_for_table(table_name: str) -> Any:
    """Discover the quality provider schema associated with a table name.

    Searches discovered Pandera schemas for a class whose metadata or naming
    convention matches the table.
    """
    try:
        from phlo_quality.cli_schema_utils import discover_pandera_schemas

        schemas = discover_pandera_schemas()
    except ImportError:
        return None

    short_name = table_name.split(".")[-1] if "." in table_name else table_name

    for name, schema_cls in schemas.items():
        cls_lower = name.lower().replace("_", "")
        table_lower = short_name.lower().replace("_", "")
        if cls_lower == table_lower or table_lower in cls_lower:
            return schema_cls
    return None


@click.group("schema-migrate")
def schema_migrate_group() -> None:
    """Schema migration between quality schemas and storage tables."""


@schema_migrate_group.command()
@click.argument("table_name")
@click.option("--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def diff(table_name: str, schema_class: str | None, fmt: str) -> None:
    """Show pending schema changes between quality schema and storage table.

    Examples:
        phlo schema-migrate diff warehouse.customers
        phlo schema-migrate diff warehouse.customers --schema-class CustomerSchema
        phlo schema-migrate diff warehouse.customers --format json
    """
    migrator = _resolve_migrator()
    extractor = _resolve_extractor()

    native_schema = _find_native_schema(table_name, schema_class)
    if native_schema is None:
        console.print(f"[red]No quality schema found for table: {table_name}[/red]")
        sys.exit(1)

    if extractor is None:
        console.print("[red]No schema extractor available. Install phlo-quality.[/red]")
        sys.exit(1)

    desired = extractor.extract(native_schema)
    plan = migrator.diff_schema(table_name=table_name, desired=desired)

    if fmt == "json":
        click.echo(json.dumps(asdict(plan), indent=2))
        return

    if not plan.changes:
        console.print(f"[green]No schema changes detected for {table_name}[/green]")
        return

    _render_plan(plan)


@schema_migrate_group.command()
@click.argument("table_name")
@click.option("--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def plan(table_name: str, schema_class: str | None, fmt: str) -> None:
    """Generate a migration plan for a table.

    Examples:
        phlo schema-migrate plan warehouse.customers
    """
    migrator = _resolve_migrator()
    extractor = _resolve_extractor()

    native_schema = _find_native_schema(table_name, schema_class)
    if native_schema is None:
        console.print(f"[red]No quality schema found for table: {table_name}[/red]")
        sys.exit(1)

    if extractor is None:
        console.print("[red]No schema extractor available. Install phlo-quality.[/red]")
        sys.exit(1)

    desired = extractor.extract(native_schema)
    migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)

    if fmt == "json":
        click.echo(json.dumps(asdict(migration_plan), indent=2))
        return

    if not migration_plan.changes:
        console.print(f"[green]No migration needed for {table_name}[/green]")
        return

    _render_plan(migration_plan)

    if migration_plan.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in migration_plan.recommendations:
            console.print(f"  • {rec}")


@schema_migrate_group.command()
@click.argument("table_name")
@click.option("--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)")
@click.option("--yes", is_flag=True, help="Auto-approve breaking changes")
@click.option("--dry-run", is_flag=True, help="Show what would be applied without executing")
def apply(table_name: str, schema_class: str | None, yes: bool, dry_run: bool) -> None:
    """Apply schema migration to a storage table.

    Safe changes are applied automatically. Breaking changes require
    confirmation (or --yes to skip the prompt).

    Examples:
        phlo schema-migrate apply warehouse.customers
        phlo schema-migrate apply warehouse.customers --yes
        phlo schema-migrate apply warehouse.customers --dry-run
    """
    migrator = _resolve_migrator()
    extractor = _resolve_extractor()

    native_schema = _find_native_schema(table_name, schema_class)
    if native_schema is None:
        console.print(f"[red]No quality schema found for table: {table_name}[/red]")
        sys.exit(1)

    if extractor is None:
        console.print("[red]No schema extractor available. Install phlo-quality.[/red]")
        sys.exit(1)

    desired = extractor.extract(native_schema)
    migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)

    if not migration_plan.changes:
        console.print(f"[green]No migration needed for {table_name}[/green]")
        return

    _render_plan(migration_plan)

    if dry_run:
        console.print("\n[yellow]Dry run — no changes applied.[/yellow]")
        return

    approved = not migration_plan.requires_approval
    if migration_plan.requires_approval:
        if yes:
            approved = True
        else:
            console.print(
                f"\n[yellow]This plan contains breaking changes "
                f"(classification: {migration_plan.classification}).[/yellow]"
            )
            approved = click.confirm("Apply breaking changes?", default=False)

    if not approved:
        console.print("[yellow]Migration cancelled.[/yellow]")
        return

    try:
        result = migrator.apply_plan(plan=migration_plan, approved=approved)
        console.print("\n[green]Migration applied successfully.[/green]")
        for key, value in result.items():
            console.print(f"  {key}: {value}")
    except Exception as exc:
        logger.exception("schema_migrate_apply_failed", table_name=table_name)
        console.print(f"[red]Migration failed: {exc}[/red]")
        sys.exit(1)


@schema_migrate_group.command()
@click.argument("table_name")
@click.option("--limit", default=10, help="Max history entries to show")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def history(table_name: str, limit: int, fmt: str) -> None:
    """Show schema version history for a table.

    Examples:
        phlo schema-migrate history warehouse.customers
        phlo schema-migrate history warehouse.customers --limit 5
        phlo schema-migrate history warehouse.customers --format json
    """
    migrator = _resolve_migrator()

    entries = migrator.get_schema_history(table_name=table_name, limit=limit)

    if fmt == "json":
        click.echo(json.dumps(entries, indent=2, default=str))
        return

    if not entries:
        console.print(f"[yellow]No schema history found for {table_name}[/yellow]")
        return

    table = Table(title=f"Schema History: {table_name}")
    table.add_column("Snapshot", style="cyan")
    table.add_column("Timestamp", style="green")
    table.add_column("Summary", style="dim")

    for entry in entries:
        table.add_row(
            str(entry.get("snapshot_id", "")),
            str(entry.get("timestamp", "")),
            str(entry.get("summary", "")),
        )

    console.print(table)


def _find_native_schema(table_name: str, schema_class: str | None) -> Any:
    """Find the native quality schema for a table."""
    if schema_class:
        try:
            from phlo_quality.cli_schema_utils import discover_pandera_schemas

            schemas = discover_pandera_schemas()
            if schema_class in schemas:
                return schemas[schema_class]
        except ImportError:
            pass
        console.print(f"[red]Schema class not found: {schema_class}[/red]")
        return None

    return _discover_schema_for_table(table_name)


def _render_plan(plan: Any) -> None:
    """Render a SchemaMigrationPlan as a rich table."""
    classification_colors = {
        "safe": "green",
        "warning": "yellow",
        "breaking": "red",
    }
    color = classification_colors.get(plan.classification, "white")

    console.print(f"\n[bold]Migration Plan: {plan.table_name}[/bold]")
    console.print(f"Classification: [{color}]{plan.classification}[/{color}]")
    console.print(f"Requires approval: {'Yes' if plan.requires_approval else 'No'}\n")

    table = Table()
    table.add_column("Field", style="cyan")
    table.add_column("Change", style="magenta")
    table.add_column("Old", style="dim")
    table.add_column("New", style="dim")
    table.add_column("Classification")

    for change in plan.changes:
        c_color = classification_colors.get(change.classification, "white")
        table.add_row(
            change.field_name,
            change.change_type,
            change.old_value or "",
            change.new_value or "",
            f"[{c_color}]{change.classification}[/{c_color}]",
        )

    console.print(table)
