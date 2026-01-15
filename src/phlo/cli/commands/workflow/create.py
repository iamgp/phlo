"""
Create workflow command.

Interactive workflow scaffolding.
"""

from __future__ import annotations

import sys

import click


@click.command("create")
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion", "transform", "quality"]),
    prompt="Workflow type",
    help="Type of workflow to create",
)
@click.option("--domain", prompt="Domain name", help="Domain name (e.g., weather, stripe, github)")
@click.option("--table", prompt="Table name", help="Table name for ingestion")
@click.option(
    "--unique-key",
    prompt="Unique key field",
    help="Field name for deduplication (e.g., id, _id)",
)
@click.option(
    "--cron",
    default="0 */1 * * *",
    prompt="Cron schedule",
    help="Cron schedule expression",
)
@click.option(
    "--api-base-url",
    prompt="API base URL (optional)",
    default="",
    help="REST API base URL",
)
@click.option(
    "--field",
    "fields",
    multiple=True,
    help="Additional schema field (name:type, name:type?, name:type!)",
)
def create_workflow_cmd(
    workflow_type: str,
    domain: str,
    table: str,
    unique_key: str,
    cron: str,
    api_base_url: str,
    fields: tuple[str, ...],
) -> None:
    """
    Create a workflow scaffold.

    Creates all necessary files for a new workflow:
    - Pandera schema file
    - Ingestion asset file
    - Test file
    - Auto-registers domain

    Examples:
        phlo workflow create
        phlo workflow create --type ingestion --domain weather --table observations
    """
    from phlo.cli.scaffold import create_ingestion_workflow

    click.echo(f"\nCreating {workflow_type} workflow for {domain}.{table}...\n")

    try:
        if workflow_type == "ingestion":
            files = create_ingestion_workflow(
                domain=domain,
                table_name=table,
                unique_key=unique_key,
                cron=cron,
                api_base_url=api_base_url or None,
                fields=list(fields),
            )

            click.echo("Created files:\n")
            for file_path in files:
                click.echo(f"  - {file_path}")

            click.echo("\nNext steps:")
            click.echo(f"  1. Edit schema: {files[0]}")
            click.echo(f"  2. Configure API: {files[1]}")
            click.echo("  3. Restart Dagster: docker restart dagster-webserver")
            click.echo(f"  4. Test: phlo test {domain}")
            click.echo(f"  5. Materialize: phlo materialize {table}")
        else:
            click.echo(f"Error: Workflow type '{workflow_type}' not yet implemented", err=True)
            click.echo("Currently supported: ingestion", err=True)
            sys.exit(1)
    except Exception as exc:
        click.echo(f"Error creating workflow: {exc}", err=True)
        sys.exit(1)
