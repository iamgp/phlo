"""PostgREST CLI commands for Phlo."""

from typing import Optional

import click

from phlo_postgrest.setup import setup_postgrest
from phlo_postgrest.views import generate_views


@click.group()
def postgrest():
    """PostgREST API management."""
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
    """Generate PostgREST API views from dbt models."""
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
        raise SystemExit(1)


@postgrest.command(name="setup-auth")
@click.option("--host", help="PostgreSQL host")
@click.option("--port", type=int, help="PostgreSQL port")
@click.option("--database", help="PostgreSQL database name")
@click.option("--user", help="PostgreSQL user")
@click.option("--password", help="PostgreSQL password")
@click.option("--force", is_flag=True, help="Force re-setup even if already exists")
@click.option("-q", "--quiet", is_flag=True, help="Suppress output")
def setup_postgrest_cmd(host, port, database, user, password, force, quiet):
    """Set up PostgREST authentication infrastructure."""
    try:
        setup_postgrest(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            force=force,
            verbose=not quiet,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
