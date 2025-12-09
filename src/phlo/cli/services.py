"""
Phlo Services Management

Manages Docker infrastructure for Phlo projects.
Creates .phlo/ directory in user projects with docker-compose configuration.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

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


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
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

    # Try configured name first
    configured_name = get_container_name("dagster_webserver", project_name)
    if configured_name:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={configured_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            return configured_name

    # Try new naming convention: {project}-dagster-1
    new_name = f"{project_name}-dagster-1"
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={new_name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return new_name

    # Try legacy naming convention: {project}-dagster-webserver-1
    legacy_name = f"{project_name}-dagster-webserver-1"
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={legacy_name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        return legacy_name

    # Try regex pattern match
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            f"name={project_name}.*dagster",
            "--format",
            "{{.Names}}",
        ],
        capture_output=True,
        text=True,
    )

    containers = [c for c in result.stdout.strip().split("\n") if c and "daemon" not in c]
    if containers:
        return containers[0]

    raise RuntimeError(
        f"Could not find running Dagster webserver container for project '{project_name}'. "
        f"Expected container name: {new_name} or {legacy_name}"
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
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    container_name,
                    "curl",
                    "-s",
                    f"{nessie_url}/api/v1/trees",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and "references" in result.stdout:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        click.echo("Warning: Nessie not ready, skipping branch initialization", err=True)
        return

    # Get existing branches
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "curl",
                "-s",
                f"{nessie_url}/api/v1/trees",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(result.stdout)
        existing = {r["name"] for r in data.get("references", [])}
    except Exception as e:
        click.echo(f"Warning: Could not check Nessie branches: {e}", err=True)
        return

    # Create dev branch from main if it doesn't exist
    if "dev" not in existing and "main" in existing:
        click.echo("Creating Nessie 'dev' branch from 'main'...")
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    container_name,
                    "curl",
                    "-s",
                    f"{nessie_url}/api/v1/trees/tree/main",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            main_data = json.loads(result.stdout)
            main_hash = main_data.get("hash", "")

            if main_hash:
                result = subprocess.run(
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
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "dev" in result.stdout:
                    click.echo("Created Nessie 'dev' branch.")
                else:
                    click.echo(
                        f"Warning: Could not create dev branch: {result.stdout}",
                        err=True,
                    )
        except Exception as e:
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
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                "cd /app/transforms/dbt && dbt deps --profiles-dir profiles",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            click.echo(f"Warning: dbt deps failed: {result.stderr}", err=True)

        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                "cd /app/transforms/dbt && dbt compile --profiles-dir profiles --target dev",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            click.echo("dbt models compiled successfully.")
            click.echo("Restarting Dagster to pick up dbt manifest...")
            subprocess.run(
                [
                    "docker",
                    "restart",
                    container_name,
                    f"{project_name}-dagster-daemon-1",
                ],
                capture_output=True,
                timeout=30,
            )
        else:
            click.echo(f"Warning: dbt compile failed: {result.stderr}", err=True)
            click.echo("You may need to run 'dbt compile' manually.", err=True)
    except subprocess.TimeoutExpired:
        click.echo("Warning: dbt compile timed out.", err=True)
    except Exception as e:
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
    "--phlo-source",
    type=click.Path(exists=True),
    help="Path to phlo source (default: auto-detect from phlo package location)",
)
def init(force: bool, project_name: Optional[str], dev: bool, phlo_source: Optional[str]):
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

    Examples:
        phlo services init
        phlo services init --name my-lakehouse
        phlo services init --force
        phlo services init --dev
        phlo services init --dev --phlo-source ../../src/phlo
    """
    from phlo.services import ComposeGenerator, ServiceDiscovery

    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if phlo_dir.exists() and not force:
        click.echo(f"Directory {phlo_dir} already exists.", err=True)
        click.echo("Use --force to overwrite.", err=True)
        sys.exit(1)

    # Derive project name from directory if not specified
    if not project_name:
        project_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")

    # Auto-detect phlo source path for dev mode
    phlo_src_path: str | None = None
    if dev:
        if phlo_source:
            # User-provided path is relative to project root, add ../ for .phlo context
            phlo_src_path = f"../{phlo_source}"
        else:
            # Try to find phlo source relative to current directory
            # Common pattern: examples/project-name -> ../../src/phlo
            candidate = Path.cwd().parent.parent / "src" / "phlo"
            if candidate.exists() and (candidate / "__init__.py").exists():
                # Path from .phlo/ directory: ../../../src/phlo
                phlo_src_path = "../../../src/phlo"
                click.echo(f"Dev mode: using phlo source at {candidate}")
            else:
                click.echo(
                    "Warning: --dev specified but could not auto-detect phlo source.", err=True
                )
                click.echo("Use --phlo-source to specify the path.", err=True)
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
    detach: bool, build: bool, profile: tuple[str, ...], dev: bool, phlo_source: Optional[str]
):
    """Start Phlo infrastructure services.

    Examples:
        phlo services start
        phlo services start --build
        phlo services start --profile observability
        phlo services start --dev
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"
    project_name = get_project_name()

    if not compose_file.exists():
        click.echo("Error: docker-compose.yml not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    if dev:
        click.echo(f"Starting {project_name} infrastructure in DEVELOPMENT mode...")
    else:
        click.echo(f"Starting {project_name} infrastructure...")

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
    ]

    for p in profile:
        cmd.extend(["--profile", p])

    cmd.append("up")

    if detach:
        cmd.append("-d")

    if build:
        cmd.append("--build")

    try:
        result = subprocess.run(cmd, check=False)
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
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        click.echo("Please install Docker: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)


@services.command("stop")
@click.option("-v", "--volumes", is_flag=True, help="Remove volumes (deletes data)")
@click.option(
    "--profile",
    multiple=True,
    help="Stop optional profile services",
)
def stop(volumes: bool, profile: tuple[str, ...]):
    """Stop Phlo infrastructure services.

    Examples:
        phlo services stop
        phlo services stop --volumes
        phlo services stop --profile observability
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"
    project_name = get_project_name()

    click.echo(f"Stopping {project_name} infrastructure...")

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
    ]

    for p in profile:
        cmd.extend(["--profile", p])

    cmd.append("down")

    if volumes:
        cmd.append("-v")
        click.echo("Warning: Removing volumes will delete all data.")

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            click.echo(f"{project_name} infrastructure stopped.")
        else:
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)


@services.command("status")
def status():
    """Show status of Phlo infrastructure services.

    Examples:
        phlo services status
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"
    project_name = get_project_name()

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
        "ps",
        "--format",
        "table {{.Name}}\t{{.Status}}\t{{.Ports}}",
    ]

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            click.echo("No services running or error checking status.", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
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
        compose_file = phlo_dir / "docker-compose.yml"
        env_file = phlo_dir / ".env"

        # Determine if we need to enable a profile
        profiles = []
        if service.profile:
            profiles = ["--profile", service.profile]

        cmd = [
            "docker",
            "compose",
            "-p",
            project_name,
            "-f",
            str(compose_file),
            "--env-file",
            str(env_file),
            *profiles,
            "up",
            "-d",
            service_name,
        ]

        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode == 0:
                click.echo(f"Service '{service_name}' started.")
            else:
                click.echo(f"Warning: Could not start {service_name}.", err=True)
        except Exception as e:
            click.echo(f"Warning: Could not start {service_name}: {e}", err=True)


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
        compose_file = phlo_dir / "docker-compose.yml"
        env_file = phlo_dir / ".env"

        click.echo(f"Stopping {service_name}...")

        profiles = []
        if service.profile:
            profiles = ["--profile", service.profile]

        cmd = [
            "docker",
            "compose",
            "-p",
            project_name,
            "-f",
            str(compose_file),
            "--env-file",
            str(env_file),
            *profiles,
            "stop",
            service_name,
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=False)
        except Exception:
            pass

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
    from phlo.services import ComposeGenerator

    all_services = discovery.discover()

    # Get default services
    default_services = discovery.get_default_services()

    # Get enabled services from config
    enabled_names = config.get("services", {}).get("enabled", [])
    disabled_names = config.get("services", {}).get("disabled", [])

    # Build final service list
    services_to_install = []
    for svc in default_services:
        if svc.name not in disabled_names:
            services_to_install.append(svc)

    # Add explicitly enabled services
    for name in enabled_names:
        if name in all_services and name not in disabled_names:
            svc = all_services[name]
            if svc not in services_to_install:
                services_to_install.append(svc)

    # Also include profile services (they're in compose but inactive unless profile enabled)
    for svc in all_services.values():
        if svc.profile and svc not in services_to_install and svc.name not in disabled_names:
            services_to_install.append(svc)

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
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"
    project_name = get_project_name()

    cmd = [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
        "logs",
        "--tail",
        str(tail),
    ]

    if follow:
        cmd.append("-f")

    if service:
        cmd.append(service)

    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
