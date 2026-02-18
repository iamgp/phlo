"""Dagster development server command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("dev")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=3000, type=int, help="Port to bind to")
@click.option("--workflows-path", default="workflows", help="Path to workflows directory")
def dev(host: str, port: int, workflows_path: str) -> None:
    """Start Dagster development server with your workflows."""
    click.echo("Starting Phlo development server...\n")
    logger.info(
        "dagster_dev_command_started",
        host=host,
        port=port,
        workflows_path=workflows_path,
    )

    if not Path("pyproject.toml").exists():
        logger.error("dagster_dev_project_not_initialized", workflows_path=workflows_path)
        click.echo("Error: No pyproject.toml found", err=True)
        click.echo("\nAre you in a Phlo project directory?", err=True)
        click.echo("Initialize a new project with: phlo init", err=True)
        sys.exit(1)

    workflows_dir = Path(workflows_path)
    if not workflows_dir.exists():
        logger.warning(
            "dagster_dev_workflows_dir_missing_creating",
            workflows_path=workflows_path,
        )
        click.echo(f"Warning: Workflows directory not found: {workflows_path}")
        click.echo("Creating empty workflows directory...")
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "__init__.py").write_text('"""User workflows."""\n')

    os.environ["PHLO_WORKFLOWS_PATH"] = workflows_path

    click.echo(f"Workflows directory: {workflows_path}")
    click.echo(f"Starting server at http://{host}:{port}\n")

    cmd = [
        "dagster",
        "dev",
        "-m",
        "phlo_dagster.framework.definitions",
        "-h",
        host,
        "-p",
        str(port),
    ]
    logger.info(
        "dagster_dev_process_launching",
        host=host,
        port=port,
        workflows_path=workflows_path,
    )

    try:
        subprocess.run(cmd, check=True)
        logger.info("dagster_dev_process_exited_cleanly")
    except KeyboardInterrupt:
        logger.info("dagster_dev_process_interrupted")
        click.echo("\n\nShutting down Dagster development server...")
    except FileNotFoundError:
        logger.error("dagster_dev_binary_not_found", binary="dagster")
        click.echo("Error: dagster command not found", err=True)
        click.echo("\nInstall Phlo with: pip install -e .", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "dagster_dev_process_failed",
            returncode=exc.returncode,
            exc_info=True,
        )
        click.echo(f"\nDagster failed with exit code {exc.returncode}", err=True)
        sys.exit(exc.returncode)
