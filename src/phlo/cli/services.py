"""
Phlo Services Management

Manages Docker infrastructure for Phlo projects.
Creates .phlo/ directory in user projects with docker-compose configuration.
"""

import os
import re
import shutil
import sys
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Optional

import click
import yaml

from phlo.cli._services.command import CommandError, run_command
from phlo.cli._services.compose import compose_base_cmd
from phlo.cli._services.containers import dagster_container_candidates, select_first_existing

PHLO_CONFIG_FILE = "phlo.yaml"

PHLO_CONFIG_TEMPLATE = """# Phlo Project Configuration
name: {name}
description: "{description}"

# Smart defaults are used for infrastructure (9 services: dagster, postgres, minio, etc.)
# Override only what you need. For example:
#
# infrastructure:
#   services:
#     postgres:
#       host: custom-host  # Override postgres host
#   container_naming_pattern: "{{project}}_{{service}}"  # Custom naming
"""


def detect_phlo_source_path() -> str | None:
    """Detect phlo source path using multiple strategies.

    Tries in order:
    1. PHLO_DEV_SOURCE environment variable
    2. Common directory patterns relative to CWD
    3. Returns None if not found

    Returns:
        Relative path to phlo source from .phlo/ directory, or None.
    """
    # Strategy 1: Environment variable
    env_path = os.environ.get("PHLO_DEV_SOURCE")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists() and (candidate / "__init__.py").exists():
            # Calculate relative path from .phlo/ to the source
            try:
                return os.path.relpath(candidate, Path.cwd() / ".phlo")
            except ValueError:
                # On Windows, relpath can fail across drives
                return str(candidate)

    # Strategy 2: Common directory patterns
    patterns = [
        # examples/project-name -> ../../src/phlo
        (Path.cwd().parent.parent / "src" / "phlo", "../../../src/phlo"),
        # src/project-name -> ../phlo
        (Path.cwd().parent / "phlo", "../../phlo"),
        # project-name/subdir -> ../src/phlo
        (Path.cwd().parent / "src" / "phlo", "../../src/phlo"),
        # At repo root -> src/phlo
        (Path.cwd() / "src" / "phlo", "../src/phlo"),
    ]

    for candidate, rel_path in patterns:
        if candidate.exists() and (candidate / "__init__.py").exists():
            return rel_path

    return None


def get_compose_dev_mode(compose_file: Path) -> bool | None:
    """Check if existing docker-compose.yml was generated in dev mode.

    Returns:
        True if dev mode, False if not, None if cannot determine.
    """
    if not compose_file.exists():
        return None

    try:
        with open(compose_file) as f:
            for _ in range(5):
                line = f.readline()
                if match := re.match(r"^# Dev mode: (true|false)", line):
                    return match.group(1) == "true"
    except OSError:
        return None

    return None


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        run_command(["docker", "info"], timeout_seconds=10, check=True)
        return True
    except (CommandError, FileNotFoundError, TimeoutExpired, OSError):
        return False


def require_docker():
    """Exit with helpful message if Docker is not running."""
    if not check_docker_running():
        click.echo("Error: Docker is not running.", err=True)
        click.echo("", err=True)
        click.echo("Please start Docker Desktop and try again.", err=True)
        click.echo("Download: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)


def get_project_config() -> dict:
    """Load project configuration from phlo.yaml.

    Returns default config if file doesn't exist.
    """
    config_path = Path.cwd() / PHLO_CONFIG_FILE
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    # Default: derive name from current directory
    return {
        "name": Path.cwd().name.lower().replace(" ", "-").replace("_", "-"),
        "description": "Phlo data lakehouse",
    }


def get_project_name() -> str:
    """Get the project name for Docker Compose."""
    config = get_project_config()
    return config.get("name", Path.cwd().name.lower().replace(" ", "-").replace("_", "-"))


def find_dagster_container(project_name: str) -> str:
    """Find the running Dagster webserver container for the project."""
    from phlo.infrastructure import get_container_name

    configured_name = get_container_name("dagster_webserver", project_name)
    candidates = dagster_container_candidates(project_name, configured_name)
    preferred = [candidates.configured, candidates.new, candidates.legacy]

    existing = run_command(["docker", "ps", "--format", "{{.Names}}"]).stdout.splitlines()
    chosen = select_first_existing(preferred, existing)
    if chosen:
        return chosen

    # Last resort: choose any container matching project + dagster, excluding daemon
    fallback_matches = [
        name
        for name in existing
        if re.search(rf"{re.escape(project_name)}.*dagster", name) and "daemon" not in name
    ]
    if fallback_matches:
        return fallback_matches[0]

    raise RuntimeError(
        f"Could not find running Dagster webserver container for project '{project_name}'. "
        f"Expected container name: {candidates.new} or {candidates.legacy}"
    )


def _init_nessie_branches(project_name: str) -> None:
    """Initialize Nessie branches (main, dev) if they don't exist."""
    import json
    import time

    container_name = f"{project_name}-nessie-1"
    nessie_url = "http://localhost:19120"

    # Wait for Nessie to be ready
    for _ in range(30):
        try:
            result = run_command(
                ["docker", "exec", container_name, "curl", "-s", f"{nessie_url}/api/v1/trees"],
                timeout_seconds=5,
                check=False,
            )
            if result.returncode == 0 and "references" in result.stdout:
                break
        except (FileNotFoundError, TimeoutExpired, OSError):
            continue
        time.sleep(1)
    else:
        click.echo("Warning: Nessie not ready, skipping branch initialization", err=True)
        return

    # Get existing branches
    try:
        result = run_command(
            ["docker", "exec", container_name, "curl", "-s", f"{nessie_url}/api/v1/trees"],
            timeout_seconds=10,
        )
        data = json.loads(result.stdout)
        existing = {r["name"] for r in data.get("references", [])}
    except (CommandError, json.JSONDecodeError, KeyError, TimeoutExpired, OSError) as e:
        click.echo(f"Warning: Could not check Nessie branches: {e}", err=True)
        return

    # Create dev branch from main if it doesn't exist
    if "dev" not in existing and "main" in existing:
        click.echo("Creating Nessie 'dev' branch from 'main'...")
        try:
            result = run_command(
                [
                    "docker",
                    "exec",
                    container_name,
                    "curl",
                    "-s",
                    f"{nessie_url}/api/v1/trees/tree/main",
                ],
                timeout_seconds=10,
            )
            main_data = json.loads(result.stdout)
            main_hash = main_data.get("hash", "")

            if main_hash:
                result = run_command(
                    [
                        "docker",
                        "exec",
                        container_name,
                        "curl",
                        "-s",
                        "-X",
                        "POST",
                        f"{nessie_url}/api/v1/trees/tree",
                        "-H",
                        "Content-Type: application/json",
                        "-d",
                        json.dumps({"type": "BRANCH", "name": "dev", "hash": main_hash}),
                    ],
                    timeout_seconds=10,
                    check=False,
                )
                if "dev" in result.stdout:
                    click.echo("Created Nessie 'dev' branch.")
                else:
                    click.echo(
                        f"Warning: Could not create dev branch: {result.stdout}",
                        err=True,
                    )
        except (CommandError, json.JSONDecodeError, TimeoutExpired, OSError) as e:
            click.echo(f"Warning: Could not create dev branch: {e}", err=True)
    elif "dev" in existing:
        click.echo("Nessie branches ready (main, dev).")


def _run_dbt_compile(project_name: str) -> None:
    """Run dbt deps + compile to generate manifest.json for Dagster."""
    import time

    dbt_project = Path.cwd() / "transforms" / "dbt"
    if not (dbt_project / "dbt_project.yml").exists():
        return

    click.echo("")
    click.echo("Compiling dbt models...")

    time.sleep(5)

    container_name = find_dagster_container(project_name)

    try:
        result = run_command(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                "cd /app/transforms/dbt && dbt deps --profiles-dir profiles",
            ],
            timeout_seconds=60,
            check=False,
        )
        if result.returncode != 0:
            click.echo(f"Warning: dbt deps failed: {result.stderr}", err=True)

        result = run_command(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                "cd /app/transforms/dbt && dbt compile --profiles-dir profiles --target dev",
            ],
            timeout_seconds=120,
            check=False,
        )
        if result.returncode == 0:
            click.echo("dbt models compiled successfully.")
            click.echo("Restarting Dagster to pick up dbt manifest...")
            run_command(
                [
                    "docker",
                    "restart",
                    container_name,
                    f"{project_name}-dagster-daemon-1",
                ],
                timeout_seconds=30,
                check=False,
            )
        else:
            click.echo(f"Warning: dbt compile failed: {result.stderr}", err=True)
            click.echo("You may need to run 'dbt compile' manually.", err=True)
    except TimeoutExpired:
        click.echo("Warning: dbt compile timed out.", err=True)
    except (CommandError, OSError) as e:
        click.echo(f"Warning: Could not compile dbt: {e}", err=True)


def get_phlo_dir() -> Path:
    """Get the .phlo directory path in current project."""
    return Path.cwd() / ".phlo"


def ensure_phlo_dir() -> Path:
    """Ensure .phlo directory exists with required files."""
    phlo_dir = get_phlo_dir()

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    return phlo_dir


def get_profile_service_names(profile_names: tuple[str, ...]) -> list[str]:
    """Get service names for the specified profiles.

    Args:
        profile_names: Tuple of profile names (e.g., ('observability', 'api'))

    Returns:
        List of service names belonging to those profiles.
    """
    if not profile_names:
        return []

    from phlo.services import ServiceDiscovery

    discovery = ServiceDiscovery()
    service_names: list[str] = []

    for profile in profile_names:
        services = discovery.get_services_by_profile(profile)
        service_names.extend(s.name for s in services)

    return service_names


@click.group()
def services():
    """Manage Phlo infrastructure services (Docker)."""
    pass


@services.command("init")
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
    help="Path to phlo source (default: auto-detect or PHLO_DEV_SOURCE env var)",
)
def init(
    force: bool,
    project_name: Optional[str],
    dev: bool,
    no_dev: bool,
    phlo_source: Optional[str],
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
    Use --no-dev to explicitly generate config without dev mounts.

    Examples:
        phlo services init
        phlo services init --name my-lakehouse
        phlo services init --force
        phlo services init --dev
        phlo services init --dev --phlo-source ../../src/phlo
        phlo services init --no-dev --force  # Regenerate without dev mode
    """
    from phlo.services import ComposeGenerator, ServiceDiscovery

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

    # --no-dev takes precedence
    if no_dev:
        dev = False

    # Derive project name from directory if not specified
    if not project_name:
        project_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")

    # Auto-detect phlo source path for dev mode using flexible detection
    phlo_src_path: str | None = None
    if dev:
        if phlo_source:
            phlo_source_path = Path(phlo_source)
            if phlo_source_path.is_absolute():
                phlo_src_path = str(phlo_source_path)
            else:
                # User-provided path is relative to project root, add ../ for .phlo context
                phlo_src_path = f"../{phlo_source}"
            click.echo(f"Dev mode: using phlo source at {phlo_source}")
        else:
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

    # Create phlo.yaml config file in project root
    config_content = PHLO_CONFIG_TEMPLATE.format(
        name=project_name,
        description=f"{project_name} data lakehouse",
    )
    config_file.write_text(config_content)
    click.echo(f"Created: {PHLO_CONFIG_FILE}")

    # Create .phlo directory
    phlo_dir.mkdir(parents=True, exist_ok=True)

    # Discover services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if not all_services:
        click.echo("Error: No services found. Check services/ directory.", err=True)
        sys.exit(1)

    # Get default services + all profile services (they're included but inactive)
    default_services = discovery.get_default_services()
    profile_services = [s for s in all_services.values() if s.profile]
    services_to_install = default_services + profile_services

    # Generate docker-compose.yml
    composer = ComposeGenerator(discovery)
    compose_content = composer.generate_compose(
        services_to_install,
        phlo_dir,
        dev_mode=dev,
        phlo_src_path=phlo_src_path,
    )

    compose_file = phlo_dir / "docker-compose.yml"
    compose_file.write_text(compose_content)
    click.echo(f"Created: {compose_file.relative_to(Path.cwd())}")

    # Generate .env
    env_content = composer.generate_env(services_to_install)
    env_file = phlo_dir / ".env"
    env_file.write_text(env_content)
    click.echo(f"Created: {env_file.relative_to(Path.cwd())}")

    # Generate .gitignore
    gitignore_file = phlo_dir / ".gitignore"
    gitignore_file.write_text(composer.generate_gitignore())
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

    profiles = discovery.get_available_profiles()
    if profiles:
        click.echo(f"Optional profiles: {', '.join(sorted(profiles))}")

    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Review .phlo/.env and adjust settings if needed")
    click.echo("  2. Run: phlo services start")
    click.echo("  3. Access services:")
    click.echo("     - Dagster:     http://localhost:3000")
    click.echo("     - Observatory: http://localhost:3001")
    click.echo("     - Superset:    http://localhost:8088")
    click.echo("     - Trino:       http://localhost:8080")
    click.echo("     - MinIO:       http://localhost:9001")
    click.echo("     - pgweb:       http://localhost:8081")


@services.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all services including optional")
def list_services(show_all: bool):
    """List available services.

    Examples:
        phlo services list
        phlo services list --all
    """
    from phlo.services import ServiceDiscovery

    discovery = ServiceDiscovery()
    all_services = discovery.list_all()

    if not all_services:
        click.echo("No services found.")
        return

    # Group by category
    categories: dict[str, list[dict]] = {}
    for svc in all_services:
        cat = svc["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(svc)

    category_order = ["core", "orchestration", "bi", "admin", "api", "observability"]

    for cat in category_order:
        if cat not in categories:
            continue

        svcs = categories[cat]
        click.echo(f"\n{cat.upper()}:")

        for svc in svcs:
            default_marker = "*" if svc["default"] else " "
            profile_info = f" [{svc['profile']}]" if svc["profile"] else ""

            if show_all or svc["default"] or not svc["profile"]:
                click.echo(f"  {default_marker} {svc['name']}: {svc['description']}{profile_info}")

    click.echo("")
    click.echo("* = installed by default")
    click.echo("[profile] = optional, enable with --profile")


@services.command("start")
@click.option("-d", "--detach", is_flag=True, default=True, help="Run in background")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option(
    "--profile",
    multiple=True,
    help="Enable optional profiles (e.g., observability, api)",
)
@click.option(
    "--service",
    multiple=True,
    help="Start only specific service(s) (e.g., --service postgres,minio or --service postgres --service minio)",
)
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
@click.option(
    "--phlo-source",
    type=click.Path(exists=True),
    help="Path to phlo source (default: auto-detect or use PHLO_DEV_SOURCE_PATH)",
)
def start(
    detach: bool,
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    dev: bool,
    phlo_source: Optional[str],
):
    """Start Phlo infrastructure services.

    Examples:
        phlo services start
        phlo services start --build
        phlo services start --profile observability
        phlo services start --service postgres
        phlo services start --dev
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    project_name = get_project_name()

    if not compose_file.exists():
        click.echo("Error: docker-compose.yml not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Check for stale compose file (dev mode mismatch)
    compose_dev_mode = get_compose_dev_mode(compose_file)
    if compose_dev_mode is not None and compose_dev_mode != dev:
        current_mode = "dev" if compose_dev_mode else "production"
        requested_mode = "dev" if dev else "production"
        click.echo("")
        click.echo(
            f"Warning: docker-compose.yml was generated in {current_mode} mode, "
            f"but you're running in {requested_mode} mode.",
            err=True,
        )
        click.echo(
            f"Run 'phlo services init --force {'--dev' if dev else '--no-dev'}' to regenerate.",
            err=True,
        )
        click.echo("")

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    # This prevents restarting already-running core services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Starting services: {', '.join(services_list)}...")
    elif dev:
        click.echo(f"Starting {project_name} infrastructure in DEVELOPMENT mode...")
    else:
        click.echo(f"Starting {project_name} infrastructure...")

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    cmd.append("up")

    if detach:
        cmd.append("-d")

    if build:
        cmd.append("--build")

    # Add specific services if specified
    if services_list:
        cmd.extend(services_list)

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            click.echo("")
            click.echo("Phlo infrastructure started.")
            click.echo("")
            click.echo("Services:")
            click.echo("  - Dagster:     http://localhost:3000")
            click.echo("  - Observatory: http://localhost:3001")
            click.echo("  - Superset:    http://localhost:8088")
            click.echo("  - Trino:       http://localhost:8080")
            click.echo("  - MinIO:       http://localhost:9001")
            click.echo("  - pgweb:       http://localhost:8081")

            if "observability" in profile:
                click.echo("")
                click.echo("Observability:")
                click.echo("  - Prometheus: http://localhost:9090")
                click.echo("  - Grafana:    http://localhost:3003")
                click.echo("  - Loki:       http://localhost:3100")

            if "api" in profile:
                click.echo("")
                click.echo("API:")
                click.echo("  - PostgREST: http://localhost:3002")
                click.echo("  - Hasura:    http://localhost:8082")

            _init_nessie_branches(project_name)
            _run_dbt_compile(project_name)
        else:
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        click.echo("Please install Docker: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("stop")
@click.option("-v", "--volumes", is_flag=True, help="Remove volumes (deletes data)")
@click.option(
    "--profile",
    multiple=True,
    help="Stop optional profile services",
)
@click.option(
    "--service",
    multiple=True,
    help="Stop only specific service(s) (e.g., --service postgres,minio or --service postgres --service minio)",
)
def stop(volumes: bool, profile: tuple[str, ...], service: tuple[str, ...]):
    """Stop Phlo infrastructure services.

    Examples:
        phlo services stop
        phlo services stop --volumes
        phlo services stop --profile observability
        phlo services stop --service postgres
        phlo services stop --service postgres,minio
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    # This prevents stopping all services when only profile services should be affected
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Stopping services: {', '.join(services_list)}...")
    else:
        click.echo(f"Stopping {project_name} infrastructure...")

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)

    if services_list:
        # Stop specific services only
        cmd.extend(["stop", *services_list])
    else:
        # Stop all services
        cmd.append("down")
        if volumes:
            cmd.append("-v")
            click.echo("Warning: Removing volumes will delete all data.")

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            if services_list:
                click.echo(f"Stopped services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure stopped.")
        else:
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("reset")
@click.option(
    "--service",
    multiple=True,
    help="Reset only specific service(s) volumes (e.g., --service postgres,minio or --service postgres --service minio)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reset(service: tuple[str, ...], yes: bool):
    """Reset Phlo infrastructure by stopping services and deleting volumes.

    This stops all services and removes their data volumes for a clean slate.
    Use --service to selectively reset only specific service volumes.

    Examples:
        phlo services reset                      # Reset everything
        phlo services reset --service postgres   # Reset only postgres
        phlo services reset --service postgres,minio  # Reset multiple
        phlo services reset -y                   # Skip confirmation
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    project_name = get_project_name()
    volumes_dir = phlo_dir / "volumes"

    if not compose_file.exists():
        click.echo("Error: docker-compose.yml not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # Determine what to reset
    if services_list:
        target = f"services: {', '.join(services_list)}"
        volume_dirs = [volumes_dir / s for s in services_list]
    else:
        target = "all services"
        volume_dirs = [volumes_dir] if volumes_dir.exists() else []

    # Confirm
    if not yes:
        click.echo(f"This will stop {target} and DELETE their data volumes.")
        if not click.confirm("Are you sure you want to continue?"):
            click.echo("Aborted.")
            return

    # Stop services - selective or all
    if services_list:
        # Stop and remove only specific services
        click.echo(f"Stopping services: {', '.join(services_list)}...")
        cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
        cmd.extend(
            [
                "rm",
                "-f",  # Force removal
                "-s",  # Stop containers if running
                "-v",  # Remove anonymous volumes
                *services_list,  # Specific services
            ]
        )
    else:
        # Stop all services
        click.echo(f"Stopping {project_name} infrastructure...")
        cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
        cmd.extend(
            [
                "down",
                "-v",  # Remove Docker volumes
            ]
        )

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo(
                f"Warning: docker compose command failed with code {result.returncode}", err=True
            )
            click.echo(f"Command: {' '.join(cmd)}", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Warning: docker compose command timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)

    # Delete local volume directories
    deleted_count = 0
    for vol_dir in volume_dirs:
        if vol_dir.exists():
            try:
                if vol_dir.is_dir():
                    shutil.rmtree(vol_dir)
                    deleted_count += 1
                    click.echo(f"Deleted: {vol_dir.relative_to(phlo_dir)}")
            except OSError as e:
                click.echo(f"Warning: Could not delete {vol_dir}: {e}", err=True)

    # Recreate volumes directory if we deleted it entirely
    if not services_list and not volumes_dir.exists():
        volumes_dir.mkdir(parents=True, exist_ok=True)

    click.echo("")
    if services_list:
        click.echo(f"Reset complete for: {', '.join(services_list)}")
    else:
        click.echo("Full reset complete. All data volumes have been deleted.")
    click.echo("Run 'phlo services start' to start fresh.")


@services.command("restart")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option(
    "--profile",
    multiple=True,
    help="Restart optional profile services (e.g., observability, api)",
)
@click.option(
    "--service",
    multiple=True,
    help="Restart only specific service(s) (e.g., --service postgres,minio)",
)
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
def restart(
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    dev: bool,
):
    """Restart Phlo infrastructure services (stop + start).

    Combines stop and start in a single command for convenience.

    Examples:
        phlo services restart                          # Restart all services
        phlo services restart --profile observability  # Restart profile services only
        phlo services restart --service postgres       # Restart specific service
        phlo services restart --build                  # Rebuild before starting
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Restarting services: {', '.join(services_list)}...")
    else:
        click.echo(f"Restarting {project_name} infrastructure...")

    # Stop services
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    if services_list:
        cmd.extend(["stop", *services_list])
    else:
        cmd.append("down")

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo(f"Warning: stop failed with code {result.returncode}", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Warning: stop timed out.", err=True)

    # Start services
    click.echo("")
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    cmd.extend(["up", "-d"])

    if build:
        cmd.append("--build")

    if services_list:
        cmd.extend(services_list)

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            click.echo("")
            if services_list:
                click.echo(f"Restarted services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure restarted.")
        else:
            click.echo(f"Error: start failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("status")
def status():
    """Show status of Phlo infrastructure services.

    Examples:
        phlo services status
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"])

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo("No services running or error checking status.", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("add")
@click.argument("service_name")
@click.option("--no-start", is_flag=True, help="Don't start the service after adding")
def add_service(service_name: str, no_start: bool):
    """Add an optional service to the project.

    Examples:
        phlo services add prometheus
        phlo services add grafana --no-start
        phlo services add hasura
    """
    from phlo.services import ServiceDiscovery

    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Load project config
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
    else:
        click.echo("Error: phlo.yaml not found.", err=True)
        sys.exit(1)

    # Discover available services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if service_name not in all_services:
        click.echo(f"Error: Service '{service_name}' not found.", err=True)
        click.echo("")
        click.echo("Available services:")
        for name in sorted(all_services.keys()):
            svc = all_services[name]
            marker = "[optional]" if svc.profile or not svc.default else "[default]"
            click.echo(f"  {name} {marker}")
        sys.exit(1)

    service = all_services[service_name]

    # Update config
    if "services" not in config:
        config["services"] = {}
    if "enabled" not in config["services"]:
        config["services"]["enabled"] = []

    enabled = config["services"]["enabled"]
    if service_name in enabled:
        click.echo(f"Service '{service_name}' is already enabled.")
        return

    enabled.append(service_name)
    config["services"]["enabled"] = sorted(set(enabled))

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Added '{service_name}' to phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)

    click.echo(f"Service '{service_name}' added.")

    if not no_start:
        click.echo("")
        click.echo(f"Starting {service_name}...")
        project_name = get_project_name()

        cmd = compose_base_cmd(
            phlo_dir=phlo_dir,
            project_name=project_name,
            profiles=() if not service.profile else (service.profile,),
        )
        cmd.extend(["up", "-d", service_name])
        try:
            result = run_command(cmd, check=False, capture_output=False)
            if result.returncode == 0:
                click.echo(f"Service '{service_name}' started.")
            else:
                click.echo(f"Warning: Could not start {service_name}.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
        except (FileNotFoundError, TimeoutExpired, OSError) as e:
            click.echo(f"Warning: Could not start {service_name}: {e}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)


@services.command("remove")
@click.argument("service_name")
@click.option("--keep-running", is_flag=True, help="Don't stop the service")
def remove_service(service_name: str, keep_running: bool):
    """Remove a service from the project.

    This removes the service from your configuration. Core services
    cannot be removed as they are required for the lakehouse to function.

    Examples:
        phlo services remove prometheus
        phlo services remove grafana --keep-running
    """
    from phlo.services import ServiceDiscovery

    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        sys.exit(1)

    # Load project config
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
    else:
        click.echo("Error: phlo.yaml not found.", err=True)
        sys.exit(1)

    # Discover available services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if service_name not in all_services:
        click.echo(f"Error: Service '{service_name}' not found.", err=True)
        sys.exit(1)

    service = all_services[service_name]

    # Prevent removing core default services
    core_services = {"postgres", "minio", "nessie", "trino", "dagster", "dagster-daemon"}
    if service_name in core_services:
        click.echo(f"Error: Cannot remove core service '{service_name}'.", err=True)
        click.echo("Core services are required for the lakehouse to function.", err=True)
        sys.exit(1)

    # Stop the service first if running
    if not keep_running:
        project_name = get_project_name()

        click.echo(f"Stopping {service_name}...")

        try:
            cmd = compose_base_cmd(
                phlo_dir=phlo_dir,
                project_name=project_name,
                profiles=() if not service.profile else (service.profile,),
            )
            cmd.extend(["stop", service_name])
            run_command(cmd, check=False, capture_output=False)
        except (FileNotFoundError, TimeoutExpired, OSError):
            click.echo(f"Warning: Could not stop {service_name}.", err=True)

    # Update config
    if "services" not in config:
        config["services"] = {}
    if "disabled" not in config["services"]:
        config["services"]["disabled"] = []
    if "enabled" not in config["services"]:
        config["services"]["enabled"] = []

    # Remove from enabled if present
    enabled = config["services"]["enabled"]
    if service_name in enabled:
        enabled.remove(service_name)

    # Add to disabled
    disabled = config["services"]["disabled"]
    if service_name not in disabled:
        disabled.append(service_name)
        config["services"]["disabled"] = sorted(set(disabled))

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Removed '{service_name}' from phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)

    click.echo(f"Service '{service_name}' removed.")


def _regenerate_compose(discovery, config: dict, phlo_dir: Path):
    """Regenerate docker-compose.yml based on current config."""
    from phlo.cli._services.selection import select_services_to_install
    from phlo.services import ComposeGenerator

    all_services = discovery.discover()

    # Get default services
    default_services = discovery.get_default_services()

    # Get enabled services from config
    enabled_names = config.get("services", {}).get("enabled", [])
    disabled_names = config.get("services", {}).get("disabled", [])

    services_to_install = select_services_to_install(
        all_services=all_services,
        default_services=default_services,
        enabled_names=enabled_names,
        disabled_names=disabled_names,
    )

    # Generate docker-compose.yml
    composer = ComposeGenerator(discovery)
    compose_content = composer.generate_compose(services_to_install, phlo_dir)

    compose_file = phlo_dir / "docker-compose.yml"
    compose_file.write_text(compose_content)
    click.echo("Updated: .phlo/docker-compose.yml")

    # Regenerate .env
    env_content = composer.generate_env(services_to_install)
    env_file = phlo_dir / ".env"
    env_file.write_text(env_content)
    click.echo("Updated: .phlo/.env")

    # Copy any new service files
    copied_files = composer.copy_service_files(services_to_install, phlo_dir)
    for f in copied_files:
        click.echo(f"Updated: .phlo/{f}")


@services.command("logs")
@click.argument("service", required=False)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
@click.option("-n", "--tail", default=100, help="Number of lines to show")
def logs(service: Optional[str], follow: bool, tail: int):
    """View logs from Phlo infrastructure services.

    Examples:
        phlo services logs
        phlo services logs dagster
        phlo services logs -f
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["logs", "--tail", str(tail)])

    if follow:
        cmd.append("-f")

    if service:
        cmd.append(service)

    try:
        run_command(cmd, check=False, capture_output=False)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker logs timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
