"""Workflow management commands."""

from __future__ import annotations

from pathlib import Path

import click

from phlo.cli.output import user_error
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
    if test_file:
        click.echo(f"  3. Run generated tests: uv run pytest {test_file} -q")
        click.echo("  4. Restart Dagster: phlo services restart --service dagster")
        click.echo(f"  5. Materialize: phlo materialize dlt_{table}")
        click.echo("  6. Inspect status: phlo status")
    else:
        click.echo("  3. Restart Dagster: phlo services restart --service dagster")
        click.echo(f"  4. Materialize: phlo materialize dlt_{table}")
        click.echo("  5. Inspect status: phlo status")


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

    validate_workflow_file(Path(path), require_workflow=True)


def _validate_schema_file(path: str) -> None:
    """Validate a schema file using the existing schema validator."""
    from phlo_pandera.cli_schema_utils import validate_schema_file

    try:
        validate_schema_file(Path(path))
    except click.ClickException:
        raise
    except Exception as exc:
        raise click.ClickException(f"Schema validation failed for {path}: {exc}") from exc


@workflow_group.command("create")
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion"]),
    default="ingestion",
    show_default=True,
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
    show_default=True,
    help="Cron schedule expression",
)
@click.option(
    "--api-base-url",
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
            error=str(exc),
        )
        raise user_error(
            "could not create workflow",
            details={
                "Workflow": workflow_type,
                "Dataset": f"{domain}.{table}",
            },
            run="phlo workflow create --help",
        ) from exc


@workflow_group.command("check")
@click.argument("workflow_file", type=click.Path(dir_okay=False))
def check_workflow_cmd(workflow_file: str) -> None:
    """Validate a workflow and its inferred schema before materialization."""
    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        raise user_error(
            "workflow file not found",
            missing=str(workflow_path),
            run="phlo workflow create",
        )

    schema_path = _infer_schema_path(workflow_path)

    _validate_workflow_file(str(workflow_path))
    click.echo(f"Workflow valid: {workflow_path}")

    if schema_path and schema_path.exists():
        try:
            _validate_schema_file(str(schema_path))
        except click.ClickException:
            raise
        except Exception as exc:
            raise click.ClickException(
                f"Schema validation failed for {schema_path}: {exc}"
            ) from exc
        click.echo(f"Schema valid: {schema_path}")
    elif schema_path:
        raise click.ClickException(f"Inferred schema file not found: {schema_path}")

    asset_key = _asset_key_from_workflow_path(workflow_path)
    click.echo(f"Next: phlo materialize {asset_key}")
