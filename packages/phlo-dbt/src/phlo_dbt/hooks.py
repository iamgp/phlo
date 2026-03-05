"""Service hooks for dbt-related setup."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from phlo.cli.infrastructure.command import CommandError, run_command
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger
from phlo_dbt.runtime_config import ensure_dbt_profile
from phlo_dbt.settings import get_settings

logger = get_logger(__name__)


def _find_dagster_container(project_name: str) -> str:
    """Resolve the Dagster webserver container via optional phlo-dagster integration."""
    try:
        from phlo_dagster.containers import find_dagster_container
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "dbt Dagster hooks require phlo-dagster. Install phlo-dbt[dagster] or phlo-dagster."
        ) from exc
    return find_dagster_container(project_name)


def compile_dbt() -> int:
    """Compile dbt models in the Dagster container when a dbt project exists.

    Returns:
        Process-style status code.
    """
    settings = get_settings()
    dbt_project_dir = Path(settings.dbt_project_dir)

    if dbt_project_dir.is_absolute():
        local_project = dbt_project_dir
        if not local_project.exists() and dbt_project_dir.parts[:2] == ("/", "app"):
            local_project = Path.cwd() / Path(*dbt_project_dir.parts[2:])
    else:
        local_project = Path.cwd() / dbt_project_dir

    if not (local_project / "dbt_project.yml").exists():
        logger.info(
            "dbt_hook_compile_skipped_project_missing",
            dbt_project_path=str(local_project),
        )
        return 0

    ensure_dbt_profile(local_project / "profiles", target="dev")

    logger.info(
        "dbt_hook_compile_started",
        dbt_project_path=str(local_project),
    )
    print("Compiling dbt models...")
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
                f"cd {Path('/app') / dbt_project_dir} && dbt deps --profiles-dir profiles",
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
            )
            print(f"Warning: dbt deps failed: {deps_result.stderr}")

        compile_result = run_command(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-c",
                f"cd {Path('/app') / dbt_project_dir} && "
                "dbt compile --profiles-dir profiles --target dev",
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
            print("dbt models compiled successfully.")
            print("Restarting Dagster to pick up dbt manifest...")
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
            )
            print(f"Warning: dbt compile failed: {compile_result.stderr}")
            print("You may need to run 'dbt compile' manually.")
    except CommandError as exc:
        logger.exception(
            "dbt_hook_compile_command_error",
            project_name=project_name,
            container_name=container_name,
        )
        print(f"Warning: Could not compile dbt: {exc}")
    except OSError as exc:
        logger.exception(
            "dbt_hook_compile_os_error",
            project_name=project_name,
            container_name=container_name,
        )
        print(f"Warning: Could not run dbt compile: {exc}")

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
