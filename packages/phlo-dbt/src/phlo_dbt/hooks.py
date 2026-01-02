"""Service hooks for dbt-related setup."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from phlo.config import get_settings
from phlo.cli._services.command import CommandError, run_command
from phlo.cli._services.utils import find_dagster_container, get_project_name


def compile_dbt() -> int:
    settings = get_settings()
    dbt_project_dir = Path(settings.dbt_project_dir)

    if dbt_project_dir.is_absolute():
        local_project = dbt_project_dir
        if not local_project.exists() and dbt_project_dir.parts[:2] == ("/", "app"):
            local_project = Path.cwd() / Path(*dbt_project_dir.parts[2:])
    else:
        local_project = Path.cwd() / dbt_project_dir

    if not (local_project / "dbt_project.yml").exists():
        return 0

    print("Compiling dbt models...")
    time.sleep(5)

    project_name = get_project_name()
    container_name = find_dagster_container(project_name)

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
            print(f"Warning: dbt compile failed: {compile_result.stderr}")
            print("You may need to run 'dbt compile' manually.")
    except CommandError as exc:
        print(f"Warning: Could not compile dbt: {exc}")
    except OSError as exc:
        print(f"Warning: Could not run dbt compile: {exc}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phlo dbt hooks")
    parser.add_argument("action", choices=["compile"])
    args = parser.parse_args()

    if args.action == "compile":
        return compile_dbt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
