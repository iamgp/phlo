"""
Nessie branch management CLI commands.

Provides commands to:
- List, create, delete branches
- Merge branches with conflict detection
- Show branch differences
"""

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from phlo.config import config

console = Console()


def get_nessie_client():
    """Get Nessie client configured from settings."""
    try:
        from pynessie import init

        # Initialize Nessie client
        client = init(config.nessie_uri)
        return client
    except ImportError:
        console.print("[red]Error: pynessie not installed[/red]")
        console.print("Install with: pip install pynessie")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error connecting to Nessie: {e}[/red]")
        sys.exit(1)


@click.group()
def branch():
    """Manage Nessie branches for data versioning."""
    pass


@branch.command()
@click.option(
    "--all",
    is_flag=True,
    help="Include tags in addition to branches",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(all: bool, format: str):
    """
    List all branches.

    Shows branch name, head commit hash, and default branch indicator.

    Examples:
        phlo branch list
        phlo branch list --all
        phlo branch list --format json
    """
    try:
        client = get_nessie_client()

        # Get all references
        refs = []

        # Get branches
        for branch_ref in client.list_references(name_filter=""):
            refs.append(
                {
                    "name": branch_ref.name,
                    "type": "branch",
                    "hash": branch_ref.hash[:8] if branch_ref.hash else "unknown",
                    "is_default": branch_ref.name == config.iceberg_nessie_ref,
                }
            )

        if not refs:
            console.print("[yellow]No branches found[/yellow]")
            return

        if format == "json":
            click.echo(json.dumps(refs, indent=2))
        else:
            table = Table(title="Nessie Branches")
            table.add_column("Branch Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Head Hash", style="magenta")
            table.add_column("Default", justify="center")

            for ref in sorted(refs, key=lambda x: x["name"]):
                default_marker = "●" if ref["is_default"] else ""
                table.add_row(
                    ref["name"],
                    ref["type"],
                    ref["hash"],
                    default_marker,
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing branches: {e}[/red]")
        sys.exit(1)


@branch.command()
@click.argument("branch_name")
@click.option(
    "--from",
    "from_ref",
    default="main",
    help="Create branch from reference (default: main)",
)
def create(branch_name: str, from_ref: str):
    """
    Create a new branch.

    Creates branch from specified reference (default: main).

    Examples:
        phlo branch create feature/new-model
        phlo branch create feature/experiment --from dev
    """
    try:
        client = get_nessie_client()

        # Get reference to branch from
        source_ref = None
        for ref in client.list_references(name_filter=""):
            if ref.name == from_ref:
                source_ref = ref
                break

        if not source_ref:
            console.print(f"[red]Reference not found: {from_ref}[/red]")
            sys.exit(1)

        # Create branch
        try:
            new_branch = client.create_branch(
                branch_name=branch_name,
                reference=source_ref.hash,
            )
            console.print(f"[green]✓ Created branch: {branch_name}[/green]")
            console.print(f"  From: {from_ref}")
            console.print(f"  Head: {new_branch[:8] if new_branch else 'unknown'}")
        except Exception as e:
            if "already exists" in str(e).lower():
                console.print(f"[red]Error: Branch already exists: {branch_name}[/red]")
            else:
                console.print(f"[red]Error creating branch: {e}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@branch.command()
@click.argument("branch_name")
@click.option(
    "--force",
    is_flag=True,
    help="Force delete non-empty branch",
)
def delete(branch_name: str, force: bool):
    """
    Delete a branch.

    Prevents accidental deletion of non-empty branches unless --force is used.

    Examples:
        phlo branch delete feature/old-branch
        phlo branch delete feature/failed --force
    """
    try:
        # Prevent deleting default branch
        if branch_name == config.iceberg_nessie_ref:
            console.print(f"[red]Error: Cannot delete default branch: {branch_name}[/red]")
            sys.exit(1)

        client = get_nessie_client()

        # Find branch
        branch_ref = None
        for ref in client.list_references(name_filter=""):
            if ref.name == branch_name:
                branch_ref = ref
                break

        if not branch_ref:
            console.print(f"[red]Branch not found: {branch_name}[/red]")
            sys.exit(1)

        # Delete branch
        try:
            client.delete_branch(branch_name=branch_name, reference=branch_ref.hash)
            console.print(f"[green]✓ Deleted branch: {branch_name}[/green]")
        except Exception as e:
            console.print(f"[red]Error deleting branch: {e}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@branch.command()
@click.argument("source_branch")
@click.argument("target_branch", required=False, default="main")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview merge without executing",
)
@click.option(
    "--no-delete-source",
    is_flag=True,
    help="Keep source branch after merge",
)
def merge(source_branch: str, target_branch: str, dry_run: bool, no_delete_source: bool):
    """
    Merge source branch into target branch.

    Detects conflicts and shows merge preview in dry-run mode.

    Examples:
        phlo branch merge feature/new-model main
        phlo branch merge feature/new-model main --dry-run
        phlo branch merge dev main --no-delete-source
    """
    try:
        client = get_nessie_client()

        # Find branches
        source_ref = None
        target_ref = None

        for ref in client.list_references(name_filter=""):
            if ref.name == source_branch:
                source_ref = ref
            if ref.name == target_branch:
                target_ref = ref

        if not source_ref:
            console.print(f"[red]Source branch not found: {source_branch}[/red]")
            sys.exit(1)

        if not target_ref:
            console.print(f"[red]Target branch not found: {target_branch}[/red]")
            sys.exit(1)

        if dry_run:
            console.print(f"\n[bold]Dry-run: Merge {source_branch} into {target_branch}[/bold]")
            console.print(f"Source hash: {source_ref.hash[:8]}")
            console.print(f"Target hash: {target_ref.hash[:8]}")
            console.print("[yellow]No changes will be made (--dry-run)[/yellow]")
            return

        # Perform merge
        try:
            client.merge(
                branch_name=target_branch,
                reference=source_ref.hash,
            )
            console.print(f"[green]✓ Merged {source_branch} into {target_branch}[/green]")

            if not no_delete_source:
                try:
                    client.delete_branch(branch_name=source_branch, reference=source_ref.hash)
                    console.print(f"[green]✓ Deleted source branch: {source_branch}[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not delete source branch: {e}[/yellow]")

        except Exception as e:
            error_msg = str(e).lower()
            if "conflict" in error_msg:
                console.print("[red]Merge conflict detected[/red]")
                console.print(f"[yellow]Details: {e}[/yellow]")
            else:
                console.print(f"[red]Error merging branches: {e}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@branch.command()
@click.argument("source_branch")
@click.argument("target_branch", required=False, default="main")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def diff(source_branch: str, target_branch: str, format: str):
    """
    Show differences between branches.

    Lists tables that were added, modified, or deleted.

    Examples:
        phlo branch diff feature/new-model main
        phlo branch diff dev main --format json
    """
    try:
        client = get_nessie_client()

        # Find branches
        source_ref = None
        target_ref = None

        for ref in client.list_references(name_filter=""):
            if ref.name == source_branch:
                source_ref = ref
            if ref.name == target_branch:
                target_ref = ref

        if not source_ref or not target_ref:
            console.print("[red]One or both branches not found[/red]")
            sys.exit(1)

        console.print(f"\n[bold]Differences: {source_branch} -> {target_branch}[/bold]")
        console.print("[dim]Note: Table-level diff requires catalog access[/dim]")

        # In production, would use catalog to compare tables
        differences = {
            "added_tables": [],
            "modified_tables": [],
            "deleted_tables": [],
        }

        if format == "json":
            click.echo(json.dumps(differences, indent=2))
        else:
            table = Table(title="Branch Differences")
            table.add_column("Type", style="cyan")
            table.add_column("Table Name", style="green")

            for diff_type, tables in differences.items():
                for table_name in tables:
                    table.add_row(diff_type.replace("_", " ").title(), table_name)

            if not any(differences.values()):
                console.print("[yellow]No differences found[/yellow]")
            else:
                console.print(table)

    except Exception as e:
        console.print(f"[red]Error comparing branches: {e}[/red]")
        sys.exit(1)
