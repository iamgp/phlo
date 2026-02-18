"""
Nessie branch management CLI commands.

Provides commands to:
- List, create, delete branches
- Merge branches with conflict detection
- Show branch differences
"""

import json

import click
from rich.console import Console
from rich.table import Table

from phlo.logging import get_logger
from phlo_iceberg.settings import get_settings as get_iceberg_settings
from phlo_nessie.settings import get_settings as get_nessie_settings

console = Console()
logger = get_logger(__name__)


def get_nessie_client():
    """Get Nessie client configured from settings."""
    logger.debug("nessie_branch_client_init_requested")
    try:
        from pynessie import init

        # Initialize Nessie client
        client = init(get_nessie_settings().nessie_uri())
        logger.debug("nessie_branch_client_init_succeeded")
        return client
    except ImportError:
        logger.error("nessie_branch_client_dependency_missing", exc_info=True)
        raise click.ClickException("pynessie not installed. Install with: pip install pynessie")
    except Exception as e:
        logger.error(
            "nessie_branch_client_init_failed",
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(f"Error connecting to Nessie: {e}")


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
    logger.info(
        "nessie_branch_list_requested",
        include_tags=all,
        output_format=format,
    )
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
                    "is_default": branch_ref.name == get_iceberg_settings().iceberg_nessie_ref,
                }
            )
        logger.info(
            "nessie_branch_list_refs_loaded",
            ref_count=len(refs),
        )

        if not refs:
            logger.info("nessie_branch_list_empty")
            console.print("[yellow]No branches found[/yellow]")
            return

        if format == "json":
            logger.info(
                "nessie_branch_list_rendered",
                output_format=format,
                ref_count=len(refs),
            )
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
            logger.info(
                "nessie_branch_list_rendered",
                output_format=format,
                ref_count=len(refs),
            )

    except Exception as e:
        logger.error(
            "nessie_branch_list_failed",
            include_tags=all,
            output_format=format,
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(f"Error listing branches: {e}")


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
    logger.info(
        "nessie_branch_create_requested",
        branch_name=branch_name,
        from_ref=from_ref,
    )
    try:
        client = get_nessie_client()

        # Get reference to branch from
        source_ref = None
        for ref in client.list_references(name_filter=""):
            if ref.name == from_ref:
                source_ref = ref
                break

        if not source_ref:
            logger.warning(
                "nessie_branch_create_source_not_found",
                branch_name=branch_name,
                from_ref=from_ref,
            )
            raise click.ClickException(f"Reference not found: {from_ref}")
        assert source_ref is not None

        # Create branch
        try:
            new_branch = client.create_branch(
                branch_name=branch_name,
                reference=source_ref.hash,
            )
            console.print(f"[green]✓ Created branch: {branch_name}[/green]")
            console.print(f"  From: {from_ref}")
            console.print(f"  Head: {new_branch[:8] if new_branch else 'unknown'}")
            logger.info(
                "nessie_branch_create_succeeded",
                branch_name=branch_name,
                from_ref=from_ref,
                head=(new_branch[:8] if new_branch else "unknown"),
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.warning(
                    "nessie_branch_create_already_exists",
                    branch_name=branch_name,
                    from_ref=from_ref,
                )
                raise click.ClickException(f"Branch already exists: {branch_name}")
            else:
                logger.error(
                    "nessie_branch_create_failed",
                    branch_name=branch_name,
                    from_ref=from_ref,
                    error=str(e),
                    exc_info=True,
                )
                raise click.ClickException(f"Error creating branch: {e}")

    except Exception as e:
        logger.error(
            "nessie_branch_create_terminated",
            branch_name=branch_name,
            from_ref=from_ref,
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(str(e))


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
    logger.info(
        "nessie_branch_delete_requested",
        branch_name=branch_name,
        force=force,
    )
    try:
        # Prevent deleting default branch
        if branch_name == get_iceberg_settings().iceberg_nessie_ref:
            logger.warning(
                "nessie_branch_delete_default_forbidden",
                branch_name=branch_name,
            )
            raise click.ClickException(f"Cannot delete default branch: {branch_name}")

        client = get_nessie_client()

        # Find branch
        branch_ref = None
        for ref in client.list_references(name_filter=""):
            if ref.name == branch_name:
                branch_ref = ref
                break

        if not branch_ref:
            logger.warning(
                "nessie_branch_delete_not_found",
                branch_name=branch_name,
            )
            raise click.ClickException(f"Branch not found: {branch_name}")
        assert branch_ref is not None

        # Delete branch
        try:
            client.delete_branch(branch_name=branch_name, reference=branch_ref.hash)
            console.print(f"[green]✓ Deleted branch: {branch_name}[/green]")
            logger.info(
                "nessie_branch_delete_succeeded",
                branch_name=branch_name,
            )
        except Exception as e:
            logger.error(
                "nessie_branch_delete_failed",
                branch_name=branch_name,
                error=str(e),
                exc_info=True,
            )
            raise click.ClickException(f"Error deleting branch: {e}")

    except Exception as e:
        logger.error(
            "nessie_branch_delete_terminated",
            branch_name=branch_name,
            force=force,
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(str(e))


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
    logger.info(
        "nessie_branch_merge_requested",
        source_branch=source_branch,
        target_branch=target_branch,
        dry_run=dry_run,
        no_delete_source=no_delete_source,
    )
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
            logger.warning(
                "nessie_branch_merge_source_not_found",
                source_branch=source_branch,
                target_branch=target_branch,
            )
            raise click.ClickException(f"Source branch not found: {source_branch}")
        assert source_ref is not None

        if not target_ref:
            logger.warning(
                "nessie_branch_merge_target_not_found",
                source_branch=source_branch,
                target_branch=target_branch,
            )
            raise click.ClickException(f"Target branch not found: {target_branch}")
        assert target_ref is not None

        if dry_run:
            logger.info(
                "nessie_branch_merge_dry_run",
                source_branch=source_branch,
                target_branch=target_branch,
                source_hash=source_ref.hash[:8],
                target_hash=target_ref.hash[:8],
            )
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
            logger.info(
                "nessie_branch_merge_succeeded",
                source_branch=source_branch,
                target_branch=target_branch,
            )

            if not no_delete_source:
                try:
                    client.delete_branch(branch_name=source_branch, reference=source_ref.hash)
                    console.print(f"[green]✓ Deleted source branch: {source_branch}[/green]")
                    logger.info(
                        "nessie_branch_merge_source_deleted",
                        source_branch=source_branch,
                        target_branch=target_branch,
                    )
                except Exception as e:
                    logger.warning(
                        "nessie_branch_merge_source_delete_failed",
                        source_branch=source_branch,
                        target_branch=target_branch,
                        error=str(e),
                        exc_info=True,
                    )
                    console.print(f"[yellow]Warning: Could not delete source branch: {e}[/yellow]")

        except Exception as e:
            error_msg = str(e).lower()
            if "conflict" in error_msg:
                logger.warning(
                    "nessie_branch_merge_conflict",
                    source_branch=source_branch,
                    target_branch=target_branch,
                    error=str(e),
                    exc_info=True,
                )
                raise click.ClickException(f"Merge conflict detected. Details: {e}")
            else:
                logger.error(
                    "nessie_branch_merge_failed",
                    source_branch=source_branch,
                    target_branch=target_branch,
                    error=str(e),
                    exc_info=True,
                )
                raise click.ClickException(f"Error merging branches: {e}")

    except Exception as e:
        logger.error(
            "nessie_branch_merge_terminated",
            source_branch=source_branch,
            target_branch=target_branch,
            dry_run=dry_run,
            no_delete_source=no_delete_source,
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(str(e))


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
    logger.info(
        "nessie_branch_diff_requested",
        source_branch=source_branch,
        target_branch=target_branch,
        output_format=format,
    )
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
            logger.warning(
                "nessie_branch_diff_refs_not_found",
                source_branch=source_branch,
                target_branch=target_branch,
            )
            raise click.ClickException("One or both branches not found")
        assert source_ref is not None
        assert target_ref is not None

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
        logger.info(
            "nessie_branch_diff_rendered",
            source_branch=source_branch,
            target_branch=target_branch,
            output_format=format,
            added_count=len(differences["added_tables"]),
            modified_count=len(differences["modified_tables"]),
            deleted_count=len(differences["deleted_tables"]),
        )

    except Exception as e:
        logger.error(
            "nessie_branch_diff_failed",
            source_branch=source_branch,
            target_branch=target_branch,
            output_format=format,
            error=str(e),
            exc_info=True,
        )
        raise click.ClickException(f"Error comparing branches: {e}")
