"""Hasura CLI commands for Phlo."""

import click
from phlo.logging import get_logger

from phlo_hasura.client import HasuraClient
from phlo_hasura.permissions import HasuraPermissionManager
from phlo_hasura.sync import HasuraMetadataSync
from phlo_hasura.track import HasuraTableTracker, auto_track

logger = get_logger(__name__)


@click.group()
def hasura() -> None:
    """Hasura GraphQL metadata management."""
    pass


@hasura.command()
@click.option(
    "--schema",
    default="api",
    help="Schema to track tables from (default: api)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Tables to exclude from tracking",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def track(schema: str, exclude: tuple, verbose: bool) -> None:
    """Auto-discover and track tables in Hasura."""
    try:
        exclude_list = list(exclude) if exclude else None

        tracker = HasuraTableTracker()
        results = tracker.track_tables(
            schema,
            exclude=exclude_list,
            verbose=verbose,
        )

        tracked = sum(1 for v in results.values() if v)
        total = len(results)

        if verbose:
            click.echo()
        click.echo(f"✓ Tracked {tracked}/{total} tables")

    except Exception as e:
        logger.exception(
            "hasura_track_failed",
            schema=schema,
            exclude_count=len(exclude),
            verbose=verbose,
        )
        raise click.ClickException(str(e))


@hasura.command()
@click.option(
    "--schema",
    default="api",
    help="Schema to set up relationships for (default: api)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def relationships(schema: str, verbose: bool) -> None:
    """Auto-create relationships from foreign keys."""
    try:
        tracker = HasuraTableTracker()
        results = tracker.setup_relationships(schema, verbose=verbose)

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        if verbose:
            click.echo()
        click.echo(f"✓ Created {successful}/{total} relationships")

    except Exception as e:
        logger.exception("hasura_relationships_failed", schema=schema, verbose=verbose)
        raise click.ClickException(str(e))


@hasura.command()
@click.option(
    "--schema",
    default="api",
    help="Schema to set up permissions for (default: api)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def permissions(schema: str, verbose: bool) -> None:
    """Set up default permissions for tracked tables."""
    try:
        tracker = HasuraTableTracker()
        results = tracker.setup_default_permissions(schema, verbose=verbose)

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        if verbose:
            click.echo()
        click.echo(f"✓ Created {successful}/{total} permissions")

    except Exception as e:
        logger.exception("hasura_permissions_failed", schema=schema, verbose=verbose)
        raise click.ClickException(str(e))


@hasura.command()
@click.option(
    "--schema",
    default="api",
    help="Schema to auto-track (default: api)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Verbose output",
)
def auto_setup(schema: str, verbose: bool) -> None:
    """Auto-track tables, set up relationships and permissions."""
    try:
        auto_track(schema, verbose=verbose)
    except Exception as e:
        logger.exception("hasura_auto_setup_failed", schema=schema, verbose=verbose)
        raise click.ClickException(str(e))


@hasura.command()
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path for metadata",
)
def export(output: str) -> None:
    """Export current Hasura metadata to file."""
    try:
        syncer = HasuraMetadataSync()
        syncer.export_metadata(output)
        click.echo(f"✓ Metadata exported to {output}")
    except Exception as e:
        logger.exception("hasura_export_failed", output_path=output)
        raise click.ClickException(str(e))


@hasura.command(name="apply")
@click.option(
    "--input",
    type=click.Path(exists=True),
    required=True,
    help="Input metadata file",
)
def apply_meta(input: str) -> None:
    """Apply Hasura metadata from file."""
    try:
        syncer = HasuraMetadataSync()
        syncer.import_metadata(input)
        click.echo(f"✓ Metadata applied from {input}")
    except Exception as e:
        logger.exception("hasura_apply_metadata_failed", input_path=input)
        raise click.ClickException(str(e))


@hasura.command()
def status() -> None:
    """Show Hasura tracking status."""
    try:
        client = HasuraClient()
        tracked = client.get_tracked_tables()

        click.echo("Tracked tables by schema:")
        click.echo()

        for schema in sorted(tracked.keys()):
            tables = tracked[schema]
            click.echo(f"  {schema}: {len(tables)} tables")
            for table in sorted(tables):
                click.echo(f"    • {table}")

    except Exception as e:
        logger.exception("hasura_status_failed")
        raise click.ClickException(str(e))


@hasura.command(name="sync-permissions")
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Permission config file (JSON/YAML)",
)
def sync_permissions(config: str) -> None:
    """Sync permissions from config file."""
    try:
        manager = HasuraPermissionManager()
        config_dict = manager.load_config(config)
        manager.sync_permissions(config_dict, verbose=True)
        click.echo("✓ Permissions synced")
    except Exception as e:
        logger.exception("hasura_sync_permissions_failed", config_path=config)
        raise click.ClickException(str(e))
