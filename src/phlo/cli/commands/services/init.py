"""Init command for initializing Phlo infrastructure."""

import os
import sys
from pathlib import Path

import click
import yaml

from phlo.cli.commands.services.utils import (
    PHLO_CONFIG_FILE,
    PHLO_CONFIG_TEMPLATE,
    _get_env_overrides,
    _warn_secret_env_overrides,
    detect_phlo_source_path,
    expand_service_dependencies,
    get_phlo_dir,
    resolve_phlo_package_dir,
)
from phlo.cli.infrastructure.utils import parse_env_file
from phlo.plugins.compose import ComposeGenerator
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery


def _expand_selected_services(
    discovery: ServiceDiscovery,
    services: list[ServiceDefinition],
) -> list[ServiceDefinition]:
    """Expand selected services with declared dependencies and setup companions."""
    return expand_service_dependencies(discovery, services)


@click.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--name", "project_name", help="Project name (default: directory name)")
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
@click.option(
    "--no-dev",
    is_flag=True,
    help="Explicitly disable dev mode (useful when regenerating without dev mounts)",
)
@click.option(
    "--phlo-source",
    type=click.Path(exists=True),
    help="Path to phlo repo root or `src/phlo` (default: auto-detect or PHLO_DEV_SOURCE env var)",
)
@click.option(
    "--service-dev",
    is_flag=True,
    help="Also apply service-specific `dev:` runtime overrides (opt-in)",
)
@click.option(
    "--profile",
    "profiles",
    multiple=True,
    help="Enable optional profile services (e.g., --profile observability --profile api)",
)
def init_cmd(
    force: bool,
    project_name: str | None,
    dev: bool,
    no_dev: bool,
    phlo_source: str | None,
    service_dev: bool,
    profiles: tuple[str, ...],
):
    """Initialize Phlo infrastructure in .phlo/ directory.

    Creates complete Docker Compose configuration for the full Phlo stack:
    - PostgreSQL, MinIO, Nessie (storage layer)
    - Trino (query engine)
    - Dagster (orchestration)
    - Observatory (data platform UI)
    - Superset (BI)
    - pgweb (database admin)
    - Optional: Prometheus, Loki, Grafana (--profile observability)
    - Optional: PostgREST, Hasura (--profile api)

    Use --dev to mount local phlo source for development iteration.
    Use --service-dev to opt into service-specific `dev:` runtimes as well.
    Use --no-dev to explicitly generate config without dev mounts.

    Examples:
        phlo services init
        phlo services init --name my-lakehouse
        phlo services init --force
        phlo services init --profile observability
        phlo services init --profile api --profile observability
        phlo services init --dev
        phlo services init --dev --phlo-source ../../src/phlo
        phlo services init --dev --service-dev
        phlo services init --no-dev --force  # Regenerate without dev mode
    """
    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if phlo_dir.exists() and not force:
        click.echo(f"Directory {phlo_dir} already exists.", err=True)
        click.echo("Use --force to overwrite.", err=True)
        sys.exit(1)

    # Handle conflicting flags
    if dev and no_dev:
        click.echo("Error: Cannot specify both --dev and --no-dev.", err=True)
        sys.exit(1)
    if service_dev and no_dev:
        click.echo("Error: Cannot specify both --service-dev and --no-dev.", err=True)
        sys.exit(1)

    # --no-dev takes precedence
    if no_dev:
        dev = False

    # Auto-enable dev mode if we can detect a local Phlo checkout and the user didn't opt out.
    phlo_src_path: str | None = None
    if not dev and not no_dev and not phlo_source and (detected := detect_phlo_source_path()):
        dev = True
        phlo_src_path = detected
        click.echo(f"Dev mode: auto-enabled (path: {phlo_src_path})")

    if service_dev and not dev:
        dev = True
        if not phlo_src_path:
            phlo_src_path = detect_phlo_source_path()

    # Derive project name from directory if not specified
    if not project_name:
        project_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")

    # Auto-detect phlo source path for dev mode using flexible detection
    if dev:
        if phlo_source:
            phlo_source_path = Path(phlo_source)
            if not phlo_source_path.is_absolute():
                phlo_source_path = (Path.cwd() / phlo_source_path).resolve()
            else:
                phlo_source_path = phlo_source_path.resolve()
            resolved_phlo_source = resolve_phlo_package_dir(phlo_source_path)
            if not resolved_phlo_source:
                click.echo(
                    "Error: --phlo-source must point to the phlo repo root or `src/phlo` package.",
                    err=True,
                )
                sys.exit(1)
            phlo_src_path = str(os.path.relpath(resolved_phlo_source, phlo_dir))
            click.echo(f"Dev mode: using phlo source at {resolved_phlo_source}")
        elif not phlo_src_path:
            # Use flexible path detection
            phlo_src_path = detect_phlo_source_path()
            if phlo_src_path:
                click.echo(f"Dev mode: auto-detected phlo source (path: {phlo_src_path})")
            else:
                click.echo(
                    "Warning: --dev specified but could not auto-detect phlo source.", err=True
                )
                click.echo(
                    "Set PHLO_DEV_SOURCE env var or use --phlo-source to specify the path.",
                    err=True,
                )
                dev = False

    # Create phlo.yaml config file in project root (only if it doesn't exist)
    if not config_file.exists():
        config_content = PHLO_CONFIG_TEMPLATE.format(
            name=project_name,
            description=f"{project_name} data lakehouse",
        )
        config_file.write_text(config_content)
        click.echo(f"Created: {PHLO_CONFIG_FILE}")
    else:
        click.echo(f"Using existing: {PHLO_CONFIG_FILE}")

    # Create .phlo directory
    phlo_dir.mkdir(parents=True, exist_ok=True)

    # Discover services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if not all_services:
        click.echo(
            "Error: No services found. Install service plugins or check entry points.",
            err=True,
        )
        sys.exit(1)

    # Load existing phlo.yaml config for user overrides
    existing_config = {}
    if config_file.exists():
        with config_file.open() as f:
            existing_config = yaml.safe_load(f) or {}
    user_overrides = existing_config.get("services", {})
    env_overrides = _get_env_overrides(existing_config)

    # Collect disabled services (those with enabled: false)
    disabled_services = {
        name
        for name, cfg in user_overrides.items()
        if isinstance(cfg, dict) and cfg.get("enabled") is False
    }

    # Collect inline custom services (those with type: inline)
    inline_services = [
        ServiceDefinition.from_inline(name, cfg)
        for name, cfg in user_overrides.items()
        if isinstance(cfg, dict) and cfg.get("type") == "inline"
    ]

    # Get default services (excluding disabled) + requested profile services + inline services
    default_services = discovery.get_default_services(disabled_services=disabled_services)
    requested_profiles = {profile.strip() for profile in profiles if profile.strip()}
    available_profiles = discovery.get_available_profiles()
    unknown_profiles = sorted(requested_profiles - available_profiles)
    if unknown_profiles:
        click.echo(
            f"Error: Unknown profile(s): {', '.join(unknown_profiles)}. "
            f"Available profiles: {', '.join(sorted(available_profiles)) or '(none)'}",
            err=True,
        )
        sys.exit(1)

    profile_services = []
    for profile in sorted(requested_profiles):
        profile_services.extend(
            [
                service
                for service in discovery.get_services_by_profile(profile)
                if service.name not in disabled_services
            ]
        )

    deduped_services: dict[str, ServiceDefinition] = {}
    for service in [*default_services, *profile_services, *inline_services]:
        deduped_services[service.name] = service
    services_to_install = _expand_selected_services(discovery, list(deduped_services.values()))
    _warn_secret_env_overrides(env_overrides, services_to_install)

    # Generate docker-compose.yml
    composer = ComposeGenerator(discovery)
    compose_content = composer.generate_compose(
        services_to_install,
        phlo_dir,
        dev_mode=dev,
        service_dev_mode=service_dev,
        phlo_src_path=phlo_src_path,
        user_overrides=user_overrides,
    )

    compose_file = phlo_dir / "docker-compose.yml"
    compose_file.write_text(compose_content)
    click.echo(f"Created: {compose_file.relative_to(Path.cwd())}")

    # Generate .env + .env.local
    env_file = phlo_dir / ".env"
    env_local_file = phlo_dir / ".env.local"
    existing_env_local = parse_env_file(env_local_file)
    env_content = composer.generate_env(services_to_install, env_overrides=env_overrides)
    env_local_content = composer.generate_env_local(
        services_to_install,
        env_overrides=env_overrides,
        existing_values=existing_env_local,
    )
    env_file.write_text(env_content)
    click.echo(f"Created: {env_file.relative_to(Path.cwd())}")
    env_local_file.write_text(env_local_content)
    click.echo(f"Created: {env_local_file.relative_to(Path.cwd())}")

    # Generate .gitignore
    gitignore_file = phlo_dir / ".gitignore"
    gitignore_file.write_text(composer.generate_gitignore(services_to_install))
    click.echo(f"Created: {gitignore_file.relative_to(Path.cwd())}")

    # Create volumes directory
    volumes_dir = phlo_dir / "volumes"
    volumes_dir.mkdir(exist_ok=True)

    # Copy service files (Dockerfiles, configs, etc.)
    copied_files = composer.copy_service_files(services_to_install, phlo_dir)
    for f in copied_files:
        click.echo(f"Created: .phlo/{f}")

    # Summary
    click.echo("")
    click.echo("Phlo infrastructure initialized.")
    click.echo("")

    default_names = sorted([s.name for s in default_services])
    click.echo(f"Default services: {', '.join(default_names)}")

    available_profiles = discovery.get_available_profiles()
    if available_profiles:
        click.echo(f"Optional profiles: {', '.join(sorted(available_profiles))}")

    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Commit non-secret defaults in phlo.yaml (env:)")
    click.echo("  2. Set secrets in .phlo/.env.local")
    click.echo("  3. Run: phlo services start")
    click.echo("  4. Inspect services with: phlo services list")
