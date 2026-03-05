"""Data migration CLI commands."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from phlo.migrations import (
    MigrationExecutionError,
    MigrationExecutor,
    MigrationSpecError,
    load_migration_spec,
    read_migration_history,
)

console = Console()


@click.group("migrate")
def migrate_group() -> None:
    """Data migration commands."""


@migrate_group.command("validate")
@click.argument("spec_file", type=click.Path(path_type=Path, dir_okay=False))
def validate(spec_file: Path) -> None:
    """Validate a migration spec without executing."""
    try:
        spec = load_migration_spec(spec_file)
    except MigrationSpecError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    executor = MigrationExecutor()
    errors = executor.validate(spec, dry_run_override=True)
    if errors:
        console.print("[red]Validation failed:[/red]")
        for error in errors:
            console.print(f"- {error}")
        sys.exit(1)

    console.print(f"[green]Migration spec is valid:[/green] {spec_file}")


@migrate_group.command("run")
@click.argument("spec_file", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--dry-run", is_flag=True, help="Validate and read without writing")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def run(spec_file: Path, dry_run: bool, fmt: str) -> None:
    """Execute a migration spec."""
    try:
        spec = load_migration_spec(spec_file)
        result = MigrationExecutor().execute(
            spec,
            dry_run_override=True if dry_run else None,
        )
    except (MigrationSpecError, MigrationExecutionError) as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(asdict(result), indent=2, default=str))
        return

    console.print(f"[green]Migration {result.status}:[/green] {result.name}")
    console.print(f"Rows read: {result.rows_read}")
    console.print(f"Rows written: {result.rows_written}")
    console.print(f"Chunks processed: {result.chunks_processed}")
    console.print(f"Duration: {result.duration_seconds:.2f}s")


@migrate_group.command("list")
@click.option(
    "--directory",
    "directory",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
    help="Directory to scan (defaults: migrations/, workflows/migrations/)",
)
def list_specs(directory: Path | None) -> None:
    """List available migration spec files."""
    candidates = [directory] if directory else [Path("migrations"), Path("workflows/migrations")]
    files: list[Path] = []

    for root in candidates:
        if root is None or not root.exists():
            continue
        files.extend(sorted(root.glob("*.yaml")))
        files.extend(sorted(root.glob("*.yml")))

    deduped = sorted(set(files))
    if not deduped:
        console.print("[yellow]No migration specs found.[/yellow]")
        return

    for path in deduped:
        click.echo(str(path))


@migrate_group.command("status")
@click.option("--limit", default=10, help="Max history entries to show")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def status(limit: int, fmt: str) -> None:
    """Show recent migration history."""
    entries = read_migration_history(limit=limit)
    if fmt == "json":
        click.echo(json.dumps(entries, indent=2, default=str))
        return

    if not entries:
        console.print("[yellow]No migration history found.[/yellow]")
        return

    table = Table(title="Recent Data Migrations")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Rows Read", justify="right")
    table.add_column("Rows Written", justify="right")
    table.add_column("Chunks", justify="right")
    table.add_column("Timestamp", style="dim")

    for entry in entries:
        raw_metadata = entry.get("metadata")
        metadata: dict[str, object]
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        table.add_row(
            str(entry.get("name", "")),
            str(entry.get("status", "")),
            str(entry.get("rows_read", 0)),
            str(entry.get("rows_written", 0)),
            str(entry.get("chunks_processed", 0)),
            str(metadata.get("timestamp", "")),
        )

    console.print(table)
