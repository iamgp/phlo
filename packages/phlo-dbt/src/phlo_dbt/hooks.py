"""Service hooks for dbt-related setup.

This module provides lifecycle hooks for dbt compilation and setup during
Phlo service operations. It handles compiling dbt models and restarting services
to pick up manifest changes, typically used during development workflows.

Example:
    >>> # Run via command line
    >>> # python -m phlo_dbt.hooks compile
    >>>
    >>> # Or use in service lifecycle
    >>> from phlo_dbt.hooks import compile_dbt
    >>> exit_code = compile_dbt()
    >>> if exit_code == 0:
    ...     print("Compilation successful")

"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from phlo.cli.infrastructure.command import CommandError, run_command
from phlo.cli.infrastructure.utils import get_project_name
from phlo.infrastructure import find_service_container
from phlo.logging import get_logger
from phlo_dbt.runtime_config import ensure_dbt_profile
from phlo_dbt.settings import get_settings

logger = get_logger(__name__)


def _find_dagster_container(project_name: str) -> str:
    """Resolve the Dagster webserver container via core infrastructure helpers."""
    return find_service_container(
        project_name=project_name,
        service_name="dagster",
        legacy_names=(f"{project_name}-dagster-webserver-1",),
        include_pattern=rf"{project_name}.*dagster",
        exclude_substrings=("daemon",),
    )


def _container_project_path(local_project: Path, project_root: Path | None = None) -> Path:
    project_root = (project_root or Path.cwd()).resolve()
    try:
        return Path("/app") / local_project.resolve().relative_to(project_root)
    except ValueError:
        return local_project


def compile_dbt() -> int:
    """Compile dbt models in the Dagster container when a dbt project exists.

    Checks for the existence of a dbt project and, if found, compiles it within
    the Dagster webserver container. This includes:
    - Installing dbt dependencies (dbt deps)
    - Compiling models (dbt compile)
    - Restarting Dagster services to pick up the new manifest

    Designed to be called as a service hook during Phlo startup or development
    workflows.

    Returns:
        Process-style status code (0 for success, non-zero for failure).
        Returns 0 if no dbt project exists.

    Raises:
        No explicit exceptions raised; errors are logged and reported via
        return code and structured log events.

    Example:
        >>> from phlo_dbt.hooks import compile_dbt
        >>> exit_code = compile_dbt()
        >>> if exit_code == 0:
        ...     print("dbt models compiled and Dagster restarted")
        ... else:
        ...     print("Warning: Compilation had issues")

    """
    settings = get_settings()
    local_project = settings.dbt_project_path
    profiles_dir = settings.dbt_profiles_path

    if not (local_project / "dbt_project.yml").exists():
        logger.info(
            "dbt_hook_compile_skipped_project_missing",
            dbt_project_path=str(local_project),
        )
        return 0

    ensure_dbt_profile(profiles_dir)
    container_project = _container_project_path(local_project)

    logger.info(
        "dbt_hook_compile_started",
        dbt_project_path=str(local_project),
    )
    time.sleep(5)

    project_name = get_project_name()
    container_name = _find_dagster_container(project_name)
    logger.info(
        "dbt_hook_compile_container_resolved",
        project_name=project_name,
        container_name=container_name,
    )

    try:
        deps_result = run_command(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                f"cd {container_project} && dbt deps --profiles-dir profiles",
            ],
            timeout_seconds=60,
            check=False,
        )
        if deps_result.returncode != 0:
            logger.warning(
                "dbt_hook_deps_failed",
                project_name=project_name,
                container_name=container_name,
                returncode=deps_result.returncode,
                stderr=deps_result.stderr,
            )

        compile_result = run_command(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                f"cd {container_project} && dbt compile --profiles-dir profiles",
            ],
            timeout_seconds=120,
            check=False,
        )
        if compile_result.returncode == 0:
            logger.info(
                "dbt_hook_compile_succeeded",
                project_name=project_name,
                container_name=container_name,
            )
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
            logger.warning(
                "dbt_hook_compile_failed",
                project_name=project_name,
                container_name=container_name,
                returncode=compile_result.returncode,
                stderr=compile_result.stderr,
            )
    except CommandError as exc:
        logger.exception(
            "dbt_hook_compile_command_error",
            project_name=project_name,
            container_name=container_name,
            error=str(exc),
        )
    except OSError as exc:
        logger.exception(
            "dbt_hook_compile_os_error",
            project_name=project_name,
            container_name=container_name,
            error=str(exc),
        )

    logger.info(
        "dbt_hook_compile_finished",
        project_name=project_name,
        container_name=container_name,
    )
    return 0


def main() -> int:
    """Run dbt hook CLI entrypoint.

    Returns:
        Process-style status code.

    """
    parser = argparse.ArgumentParser(description="Phlo dbt hooks")
    parser.add_argument("action", choices=["compile"])
    args = parser.parse_args()

    if args.action == "compile":
        return compile_dbt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
