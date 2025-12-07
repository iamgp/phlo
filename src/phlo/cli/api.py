"""API layer management commands (PostgREST and Hasura).

These commands are registered as subgroups under the existing 'api' command
in the main CLI (see cli/main.py).
"""

from typing import Optional

import click

from phlo.api.hasura.client import HasuraClient
from phlo.api.hasura.permissions import HasuraPermissionManager
from phlo.api.hasura.sync import HasuraMetadataSync
from phlo.api.hasura.track import HasuraTableTracker, auto_track
from phlo.api.postgrest.views import generate_views

# --- PostgREST Commands ---


@click.group()
def postgrest():
    """PostgREST API view generation."""
    pass


@postgrest.command(name="generate-views")
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
@click.option(
    "--apply",
    is_flag=True,
    help="Apply views directly to database",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show diff of changes only",
)
@click.option(
    "--models",
    type=str,
    help="Filter models by pattern (e.g., mrt_*)",
)
@click.option(
    "--schema",
    default="api",
    help="API schema name (default: api)",
)
def generate_postgrest_views(
    output: Optional[str],
    apply: bool,
    diff: bool,
    models: Optional[str],
    schema: str,
):
    """Generate PostgREST API views from dbt models.

    Examples:
        phlo api postgrest generate-views                 # Print SQL
        phlo api postgrest generate-views --output views.sql
        phlo api postgrest generate-views --apply         # Apply to DB
        phlo api postgrest generate-views --diff          # Show changes
        phlo api postgrest generate-views --models mrt_*  # Filter models
    """
    try:
        result = generate_views(
            output=output,
            apply=apply,
            diff=diff,
            models=models,
            api_schema=schema,
            verbose=True,
        )

        if not apply and not output:
            click.echo(result)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


# --- Hasura Commands ---


@click.group()
def hasura():
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
def track(schema: str, exclude: tuple, verbose: bool):
    """Auto-discover and track tables in Hasura.

    Examples:
        phlo api hasura track                   # Track tables in api schema
        phlo api hasura track --schema marts    # Track specific schema
        phlo api hasura track --exclude temp_*  # Exclude patterns
    """
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
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


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
def relationships(schema: str, verbose: bool):
    """Auto-create relationships from foreign keys.

    Examples:
        phlo api hasura relationships             # Setup in api schema
        phlo api hasura relationships --schema marts
    """
    try:
        tracker = HasuraTableTracker()
        results = tracker.setup_relationships(schema, verbose=verbose)

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        if verbose:
            click.echo()
        click.echo(f"✓ Created {successful}/{total} relationships")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


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
def permissions(schema: str, verbose: bool):
    """Set up default permissions for tracked tables.

    Examples:
        phlo api hasura permissions             # Setup in api schema
        phlo api hasura permissions --schema marts
    """
    try:
        tracker = HasuraTableTracker()
        results = tracker.setup_default_permissions(schema, verbose=verbose)

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        if verbose:
            click.echo()
        click.echo(f"✓ Created {successful}/{total} permissions")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


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
def auto_setup(schema: str, verbose: bool):
    """Auto-track tables, set up relationships and permissions.

    Combines track, relationships, and permissions in one command.

    Examples:
        phlo api hasura auto-setup             # Setup api schema
        phlo api hasura auto-setup --schema marts
    """
    try:
        auto_track(schema, verbose=verbose)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@hasura.command()
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path for metadata",
)
def export(output: str):
    """Export current Hasura metadata to file.

    Examples:
        phlo api hasura export --output metadata.json
    """
    try:
        syncer = HasuraMetadataSync()
        syncer.export_metadata(output)
        click.echo(f"✓ Metadata exported to {output}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@hasura.command()
@click.option(
    "--input",
    type=click.Path(exists=True),
    required=True,
    help="Input metadata file",
)
def apply_meta(input: str):
    """Apply Hasura metadata from file.

    Examples:
        phlo api hasura apply --input metadata.json
    """
    try:
        syncer = HasuraMetadataSync()
        syncer.import_metadata(input)
        click.echo(f"✓ Metadata applied from {input}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@hasura.command()
def status():
    """Show Hasura tracking status.

    Examples:
        phlo api hasura status
    """
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
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)


@hasura.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Permission config file (JSON/YAML)",
)
def sync_permissions(config: str):
    """Sync permissions from config file.

    Examples:
        phlo api hasura sync-permissions --config permissions.yaml
    """
    try:
        manager = HasuraPermissionManager()
        config_dict = manager.load_config(config)
        manager.sync_permissions(config_dict, verbose=True)
        click.echo("✓ Permissions synced")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(1)
