"""
Phlo CLI Main Entry Point

Provides command-line interface for Phlo workflows.
"""

import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import click

import phlo.cli._warning_filters  # noqa: F401
from phlo.cli.commands.doctor import doctor_cmd
from phlo.cli.templates import TemplateRenderContext, get_template
from phlo.cli.templates import list_templates as get_project_templates
from phlo.cli.templates.registry import missing_required_packages
from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__, service="phlo-cli")


def _is_doctor_invocation(argv: list[str]) -> bool:
    for token in argv[1:]:
        if token == "--":
            return False
        if token in {"--help", "-h", "--version"}:
            return False
        if token.startswith("-"):
            continue
        return token == "doctor"
    return False


_DOCTOR_INVOCATION = _is_doctor_invocation(sys.argv)

if not _DOCTOR_INVOCATION:
    from phlo.cli.commands.authz import authz_group
    from phlo.cli.commands.compliance import compliance_group
    from phlo.cli.commands.metrics import metrics_group
    from phlo.cli.commands.migrate import migrate_group
    from phlo.cli.commands.plugin import plugin_group
    from phlo.cli.commands.schema_migrate import schema_migrate_group
    from phlo.cli.commands.schema_registry_cli import contracts
    from phlo.cli.commands.services import _register_commands as _register_service_commands
    from phlo.cli.commands.services import services_group
    from phlo.cli.commands.workflow import workflow_group
    from phlo.cli.config import config
    from phlo.cli.env import env


@click.group()
@click.version_option(version=version("phlo"), prog_name="phlo")
def cli() -> None:
    """
    Phlo - Modern Data Lakehouse Framework

    Build production-ready data pipelines with minimal boilerplate.

    Documentation: https://github.com/iamgp/phlo
    """
    setup_logging()


cli.add_command(doctor_cmd)

if not _DOCTOR_INVOCATION:
    cli.add_command(services_group)
    cli.add_command(workflow_group)
    cli.add_command(plugin_group)
    cli.add_command(schema_migrate_group)
    cli.add_command(migrate_group)
    cli.add_command(metrics_group)
    cli.add_command(contracts)
    cli.add_command(config)
    cli.add_command(env)
    cli.add_command(authz_group)
    cli.add_command(compliance_group)


def _load_cli_plugin_commands() -> None:
    from phlo.plugins.discovery import discover_plugins, get_global_registry

    logger.debug("cli_plugin_discovery_started")
    discover_plugins(plugin_type="cli_commands", auto_register=True, failure_level="debug")
    registry = get_global_registry()
    added_count = 0
    for name in registry.list_cli_command_plugins():
        plugin = registry.get_cli_command_plugin(name)
        if plugin is None:
            logger.warning("cli_plugin_missing_in_registry", plugin_name=name)
            continue
        for command in plugin.get_cli_commands():
            if command.name is None or command.name in cli.commands:
                logger.debug("cli_command_skipped", plugin_name=name, command_name=command.name)
                continue
            cli.add_command(command)
            added_count += 1
            logger.debug("cli_command_added", plugin_name=name, command_name=command.name)
    logger.debug("cli_plugin_discovery_completed", command_count=added_count)


if not _DOCTOR_INVOCATION:
    _register_service_commands()
    _load_cli_plugin_commands()


@cli.command()
@click.argument("asset_name", required=False)
@click.option("--local", is_flag=True, help="Run tests locally without Docker")
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-m", "--marker", help="Run tests with specific pytest marker")
def test(
    asset_name: str | None,
    local: bool,
    coverage: bool,
    verbose: bool,
    marker: str | None,
):
    """
    Run tests for Phlo workflows.

    Examples:
        phlo test                          # Run all tests
        phlo test weather_observations     # Run tests for specific asset
        phlo test --local                  # Run without Docker
        phlo test --coverage               # Generate coverage report
        phlo test -m integration           # Run integration tests only
    """
    click.echo("Running Phlo tests...\n")

    # Build pytest command
    pytest_args = ["pytest"]

    if asset_name:
        # Run tests for specific asset
        test_file = f"tests/test_{asset_name}.py"
        if Path(test_file).exists():
            pytest_args = ["pytest", test_file]
        else:
            logger.warning("test_file_not_found", test_file=test_file)
            click.echo(f"Error: Test file not found: {test_file}", err=True)
            click.echo("\nAvailable test files:", err=True)
            for f in Path("tests").glob("test_*.py"):
                click.echo(f"  - {f.name}", err=True)
            sys.exit(1)

    if marker and local:
        pytest_args.extend(["-m", f"({marker}) and not integration"])
    elif marker:
        pytest_args.extend(["-m", marker])
    elif local:
        pytest_args.extend(["-m", "not integration"])

    if local:
        os.environ["PHLO_TEST_LOCAL"] = "1"
        click.echo("Local test mode enabled (PHLO_TEST_LOCAL=1)\n")

    if verbose:
        pytest_args.append("-v")

    if coverage:
        pytest_args.extend(["--cov=phlo", "--cov-report=html", "--cov-report=term"])

    # Run pytest
    try:
        result = subprocess.run(pytest_args, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        logger.error("pytest_binary_not_found")
        click.echo("Error: pytest not found. Install with: pip install pytest", err=True)
        sys.exit(1)


@cli.command("init")
@click.argument("project_name", required=False)
@click.option(
    "--template",
    default="basic",
    help="Project template to use",
)
@click.option("--force", is_flag=True, help="Initialize in non-empty directory")
@click.option("--list-templates", is_flag=True, help="List available project templates and exit.")
def init(project_name: str | None, template: str, force: bool, list_templates: bool):
    """
    Initialize a new Phlo project.

    Creates a minimal project structure for using Phlo as an installable package.
    Users only need to maintain workflow files, not the entire framework.

    Examples:
        phlo init my-data-project          # Create new project directory
        phlo init . --force                # Initialize in current directory
        phlo init weather-pipeline --template minimal
    """
    if list_templates:
        for item in get_project_templates():
            packages = ", ".join(item.metadata.required_packages)
            click.echo(f"{item.metadata.name:<20} {item.metadata.description:<36} {packages}")
        return

    click.echo("Phlo Project Initializer\n")

    # Determine project directory and metadata-safe project name
    if project_name is None or project_name == ".":
        project_dir = Path.cwd()
        project_metadata_name = project_dir.name
        click.echo(f"Initializing in current directory: {project_dir}")
    else:
        requested_path = Path(project_name).expanduser()
        project_dir = (
            requested_path if requested_path.is_absolute() else (Path.cwd() / requested_path)
        )
        project_metadata_name = project_dir.name
        click.echo(f"Creating new project: {project_dir}")

    # Check if directory exists and is not empty
    if project_dir.exists() and any(project_dir.iterdir()) and not force:
        click.echo(f"\nError: Directory {project_dir} is not empty", err=True)
        click.echo("Use --force to initialize anyway", err=True)
        sys.exit(1)

    # Create project structure
    try:
        selected_template = _create_project_structure(project_dir, project_metadata_name, template)

        click.echo(f"\nSuccessfully initialized Phlo project: {project_dir}\n")
        click.echo("Created structure:")
        click.echo(f"  {project_dir}/")
        click.echo("  ├── phlo.yaml            # Project configuration with infrastructure")
        click.echo("  ├── pyproject.toml       # Project dependencies")
        click.echo("  ├── .env.example         # Local secrets template (copy to .phlo/.env.local)")
        click.echo("  ├── .sqlfluff            # SQL linting configuration for dbt models")
        click.echo("  ├── workflows/           # Your workflow definitions")
        click.echo("  │   ├── ingestion/       # Data ingestion workflows")
        click.echo("  │   ├── schemas/         # Pandera validation schemas")
        click.echo("  │   └── transforms/dbt/  # dbt transformation models")
        click.echo("  └── tests/               # Workflow tests")

        click.echo("\nNext steps:")
        step_number = 1
        if project_dir != Path.cwd():
            click.echo(f"  {step_number}. cd {project_dir}")
            step_number += 1
        for next_step in selected_template.metadata.next_steps:
            click.echo(f"  {step_number}. {next_step}")
            step_number += 1

        click.echo("\nDocumentation: https://github.com/iamgp/phlo")

    except click.ClickException:
        raise
    except Exception as e:
        logger.exception("project_initialization_failed", project_dir=str(project_dir))
        click.echo(f"\nError initializing project: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _create_project_structure(project_dir: Path, project_name: str, template: str):
    """
    Create project directory structure and files.

    Args:
        project_dir: Path to project directory
        project_name: Name of the project
        template: Template type ("basic" or "minimal")
    """
    selected_template = get_template(template)
    missing = missing_required_packages(selected_template)
    if missing:
        packages = " ".join(missing)
        raise click.ClickException(
            f"Template '{template}' requires missing package(s): {', '.join(missing)}. "
            f"Install with: uv pip install {packages}"
        )
    selected_template.render(
        TemplateRenderContext(project_dir=project_dir, project_name=project_name)
    )
    return selected_template


def _build_env_example_content() -> str:
    from phlo.plugins.discovery import ServiceDiscovery

    lines = [
        "# Phlo Local Secrets Template",
        "# Copy to .phlo/.env.local after running `phlo services init`.",
        "",
    ]

    discovery = ServiceDiscovery()
    services = discovery.discover()
    if not services:
        lines.append(
            "# No service plugins discovered; install service packages to populate secrets."
        )
        return "\n".join(lines) + "\n"

    for service in sorted(services.values(), key=lambda s: s.name):
        secrets = {key: cfg for key, cfg in service.env_vars.items() if cfg.get("secret") is True}
        if not secrets:
            continue
        lines.append(f"# {service.name}")
        for key in sorted(secrets.keys()):
            desc = secrets[key].get("description")
            if desc:
                lines.append(f"# {desc}")
            lines.append(f"{key}=")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
