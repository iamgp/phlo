"""Development server command for local Dagster development.

This module implements the `phlo dev` CLI command, which starts a local
Dagster development server for iterative workflow development. It wraps
the `dagster dev` command with Phlo-specific configuration.

Features:
    - Automatic workflows directory creation
    - Project validation (pyproject.toml check)
    - Configurable host and port binding
    - Environment variable injection for Phlo configuration
    - Keyboard interrupt handling for clean shutdown
    - Process lifecycle logging

Environment Setup:
    Sets PHLO_WORKFLOWS_PATH to enable framework definitions discovery.
    Validates project structure before starting server.

Requirements:
    - pyproject.toml in current directory
    - Dagster installed in environment
    - Workflows directory (auto-created if missing)

Example:
    CLI usage::

        phlo dev                                    # Default host/port
        phlo dev --host 0.0.0.0 --port 8080        # Custom binding
        phlo dev --workflows-path custom_workflows  # Non-standard path

"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from phlo.config.env import load_project_env
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("dev")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=3000, type=int, help="Port to bind to")
@click.option("--workflows-path", default="workflows", help="Path to workflows directory")
def dev(host: str, port: int, workflows_path: str) -> None:
    """Start Dagster development server with your workflows.

    Args:
        host: Host address to bind the server to.
        port: Port number to bind the server to.
        workflows_path: Path to the workflows directory.

    Returns:
        None

    Raises:
        SystemExit: If pyproject.toml not found or dagster command fails.

    """
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
    os.environ["WORKFLOWS_PATH"] = workflows_path
    os.environ.setdefault("PHLO_DAGSTER_DEV", "1")
    os.environ.setdefault("PHLO_PROJECT_PATH", str(Path.cwd().resolve()))
    for key, value in load_project_env(include_os=False).items():
        os.environ.setdefault(key, value)

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
