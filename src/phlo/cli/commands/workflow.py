"""Workflow management commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from phlo.logging import get_logger

logger = get_logger(__name__)


@click.group(name="workflow")
def workflow_group() -> None:
    """Manage workflows."""


def _print_ingestion_next_steps(files: list[str], *, table: str) -> None:
    """Print the next commands for a generated ingestion workflow."""
    schema_file = files[0]
    workflow_file = files[1]
    test_file = files[2] if len(files) > 2 else None

    click.echo("\nNext steps:")
    click.echo(f"  1. Review schema: {schema_file}")
    click.echo(f"  2. Review workflow: {workflow_file}")
    click.echo(f"  3. Validate schema: phlo schema validate {schema_file}")
    click.echo(f"  4. Validate workflow: phlo validate-workflow {workflow_file}")
    if test_file:
        click.echo(f"  5. Run generated tests: uv run pytest {test_file} -q")
        click.echo("  6. Restart Dagster: phlo services restart dagster")
        click.echo(f"  7. Materialize: phlo materialize dlt_{table}")
        click.echo(f"  8. Inspect status: phlo status --select dlt_{table}")
    else:
        click.echo("  5. Restart Dagster: phlo services restart dagster")
        click.echo(f"  6. Materialize: phlo materialize dlt_{table}")
        click.echo(f"  7. Inspect status: phlo status --select dlt_{table}")


def _infer_schema_path(workflow_path: Path) -> Path | None:
    """Infer a domain schema path from a workflow path."""
    parts = workflow_path.parts
    if "workflows" not in parts or "ingestion" not in parts:
        return None
    workflows_index = parts.index("workflows")
    ingestion_index = parts.index("ingestion")
    if ingestion_index + 1 >= len(parts):
        return None
    domain = parts[ingestion_index + 1]
    root = Path(*parts[:workflows_index]) if workflows_index > 0 else Path()
    return root / "workflows" / "schemas" / f"{domain}.py"


def _asset_key_from_workflow_path(workflow_path: Path) -> str:
    """Infer the DLT asset key from a workflow file path."""
    return f"dlt_{workflow_path.stem}"


def _validate_workflow_file(path: str) -> None:
    """Validate a workflow file using the existing Pandera validator."""
    from phlo_pandera.cli_validate import validate_workflow_file

    validate_workflow_file(Path(path))


def _validate_schema_file(path: str) -> None:
    """Validate a schema file using the existing schema validator."""
    from phlo_pandera.cli_schema_utils import validate_schema_file

    validate_schema_file(Path(path))


@workflow_group.command("create")
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion"]),
    prompt="Workflow type",
    help="Type of workflow to create (ingestion only)",
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
    """Create a workflow scaffold."""
    from phlo_dlt.scaffold import create_ingestion_workflow

    logger.info(
        "workflow_create_started",
        workflow_type=workflow_type,
        domain=domain,
        table=table,
        field_count=len(fields),
    )
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

            _print_ingestion_next_steps(files, table=table)
            logger.info(
                "workflow_create_succeeded",
                workflow_type=workflow_type,
                domain=domain,
                table=table,
                file_count=len(files),
            )
    except Exception as exc:
        logger.exception(
            "workflow_create_failed",
            workflow_type=workflow_type,
            domain=domain,
            table=table,
        )
        click.echo(f"Error creating workflow: {exc}", err=True)
        sys.exit(1)


@workflow_group.command("check")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
def check_workflow_cmd(workflow_file: str) -> None:
    """Validate a workflow and its inferred schema before materialization."""
    workflow_path = Path(workflow_file)
    schema_path = _infer_schema_path(workflow_path)

    _validate_workflow_file(str(workflow_path))
    click.echo(f"Workflow valid: {workflow_path}")

    if schema_path and schema_path.exists():
        _validate_schema_file(str(schema_path))
        click.echo(f"Schema valid: {schema_path}")
    elif schema_path:
        raise click.ClickException(f"Inferred schema file not found: {schema_path}")

    asset_key = _asset_key_from_workflow_path(workflow_path)
    click.echo(f"Next: phlo materialize {asset_key}")
