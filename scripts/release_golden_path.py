#!/usr/bin/env python3
"""Run the Phlo release artifact golden path in an owned temporary project."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path

PARTITION = "2025-01-15"
PORT_NAMES = (
    "POSTGRES_PORT",
    "MINIO_API_PORT",
    "MINIO_CONSOLE_PORT",
    "NESSIE_PORT",
    "TRINO_PORT",
    "DAGSTER_PORT",
)


@dataclass(frozen=True)
class RunConfig:
    repo_root: Path
    project_dir: Path
    wheelhouse: Path
    operator_env: Path
    project_name: str
    partition: str = PARTITION

    @property
    def operator_python(self) -> Path:
        return venv_executable(self.operator_env, "python")

    @property
    def operator_bin(self) -> Path:
        return venv_executable(self.operator_env, "phlo")

    @property
    def project_env(self) -> Path:
        return self.project_dir / ".venv"

    @property
    def project_python(self) -> Path:
        return venv_executable(self.project_env, "python")

    @property
    def compose_file(self) -> Path:
        return self.project_dir / ".phlo" / "docker-compose.yml"


def venv_executable(environment: Path, executable: str) -> Path:
    """Return a virtualenv executable path for the current platform."""
    if os.name == "nt":
        candidates = (
            environment / "Scripts" / f"{executable}.exe",
            environment / "Scripts" / executable,
            environment / "bin" / executable,
        )
    else:
        candidates = (
            environment / "bin" / executable,
            environment / "Scripts" / f"{executable}.exe",
            environment / "Scripts" / executable,
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def command(*parts: str) -> list[str]:
    """Return a subprocess command as a list, keeping shell interpolation out."""
    return list(parts)


def compose_command(config: RunConfig, *parts: str) -> list[str]:
    """Build a project-scoped Docker Compose command."""
    return command(
        "docker",
        "compose",
        "-p",
        config.project_name,
        "--file",
        str(config.compose_file),
        "--env-file",
        str(config.project_dir / ".phlo" / ".env"),
        "--env-file",
        str(config.project_dir / ".phlo" / ".env.local"),
        *parts,
    )


def project_name() -> str:
    """Return a globally unique Compose project name for one harness run."""
    return f"phlo-qa001-{uuid.uuid4().hex}"


def run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one command and stream its output."""
    print(f"+ {' '.join(args)}", flush=True)
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=capture_output,
        text=True,
    )


def force_local_install(config: RunConfig, python: Path, *packages: str) -> None:
    run(
        command(
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            "--no-index",
            "--no-deps",
            "--reinstall",
            "--find-links",
            str(config.wheelhouse),
            *packages,
        ),
        cwd=config.repo_root,
    )


def build_wheelhouse(config: RunConfig) -> None:
    config.wheelhouse.mkdir(parents=True, exist_ok=True)
    run(
        command("uv", "build", "--all-packages", "--wheel", "--out-dir", str(config.wheelhouse)),
        cwd=config.repo_root,
    )
    with tempfile.NamedTemporaryFile(
        prefix="phlo-wheelhouse-", suffix=".txt", delete=False
    ) as handle:
        requirements = Path(handle.name)
    try:
        run(
            command(
                "uv",
                "export",
                "--locked",
                "--all-packages",
                "--all-extras",
                "--no-dev",
                "--no-emit-workspace",
                "--no-hashes",
                "--format",
                "requirements.txt",
                "--output-file",
                str(requirements),
            ),
            cwd=config.repo_root,
        )
        for target in dependency_wheel_targets():
            run(
                command(
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    "--disable-pip-version-check",
                    "--only-binary=:all:",
                    "--dest",
                    str(config.wheelhouse),
                    *target,
                    "--requirement",
                    str(requirements),
                ),
                cwd=config.repo_root,
            )
    finally:
        requirements.unlink(missing_ok=True)


def dependency_wheel_targets() -> tuple[tuple[str, ...], ...]:
    """Return host and Docker Linux wheel targets for the built artifact set."""
    if os.name == "nt":
        host = (
            "--platform",
            "win_amd64",
            "--python-version",
            "3.11",
            "--implementation",
            "cp",
            "--abi",
            "cp311",
        )
    elif sys.platform == "darwin":
        host = ("--python-version", "3.11", "--implementation", "cp", "--abi", "cp311")
    else:
        host = (
            "--platform",
            "manylinux_2_17_x86_64",
            "--python-version",
            "3.11",
            "--implementation",
            "cp",
            "--abi",
            "cp311",
        )
    docker = (
        "--platform",
        "manylinux_2_17_x86_64",
        "--platform",
        "manylinux_2_28_x86_64",
        "--python-version",
        "3.12",
        "--implementation",
        "cp",
        "--abi",
        "cp312",
    )
    return (host,) if host == docker else (host, docker)


def install_operator(config: RunConfig) -> None:
    run(command("uv", "venv", str(config.operator_env), "--python", "3.11"), cwd=config.repo_root)
    run(
        command(
            "uv",
            "pip",
            "install",
            "--python",
            str(config.operator_python),
            "--no-index",
            "--no-deps",
            "--find-links",
            str(config.wheelhouse),
            "phlo",
        ),
        cwd=config.repo_root,
    )
    run(
        command(
            "uv",
            "pip",
            "install",
            "--python",
            str(config.operator_python),
            "--no-index",
            "--find-links",
            str(config.wheelhouse),
            "phlo[core-services]",
            "phlo-dlt",
            "phlo-pandera",
        ),
        cwd=config.repo_root,
    )
    force_local_install(
        config,
        config.operator_python,
        "phlo",
        "phlo-dlt",
        "phlo-pandera",
    )


def create_project(config: RunConfig) -> None:
    run(
        command(
            str(config.operator_bin),
            "init",
            str(config.project_dir),
            "--template",
            "csv-batch",
        ),
        cwd=config.repo_root,
    )


def align_project_name(config: RunConfig) -> None:
    """Make generated CLI project discovery use the owned Compose project name."""
    config_file = config.project_dir / "phlo.yaml"
    lines = config_file.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("name:"):
            lines[index] = f"name: {config.project_name}\n"
            config_file.write_text("".join(lines), encoding="utf-8")
            return
    raise RuntimeError(f"generated project config has no name: {config_file}")


def install_project_dependencies(config: RunConfig) -> None:
    run(command("uv", "venv", str(config.project_env), "--python", "3.11"), cwd=config.project_dir)
    run(
        command(
            "uv",
            "pip",
            "install",
            "--python",
            str(config.project_python),
            "--no-index",
            "--find-links",
            str(config.wheelhouse),
            "phlo-dlt",
            "phlo-pandera",
        ),
        cwd=config.project_dir,
    )
    force_local_install(
        config,
        config.project_python,
        "phlo-dlt",
        "phlo-pandera",
    )


def configure_non_dev_compose(config: RunConfig) -> None:
    run(
        command(str(config.operator_bin), "services", "init", "--no-dev", "--force"),
        cwd=config.project_dir,
    )
    destination = config.project_dir / ".phlo" / "wheelhouse"
    shutil.copytree(config.wheelhouse, destination)
    with (config.repo_root / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    env_local = config.project_dir / ".phlo" / ".env.local"
    with env_local.open("a", encoding="utf-8") as stream:
        stream.write(f"\nPHLO_VERSION={version}\nPHLO_WHEELHOUSE=wheelhouse\n")
        stream.writelines(f"{name}=0\n" for name in PORT_NAMES)


def start_stack(config: RunConfig) -> None:
    try:
        run(compose_command(config, "up", "--detach", "--build"), cwd=config.project_dir)
    except subprocess.CalledProcessError:
        for parts in (("ps",), ("logs", "--no-color", "--timestamps")):
            try:
                run(compose_command(config, *parts), cwd=config.project_dir)
            except Exception as exc:
                print(f"release golden path diagnostics failed: {exc}", file=sys.stderr)
        raise


def materialize_partition(config: RunConfig) -> None:
    run(
        command(
            str(config.operator_bin),
            "materialize",
            "dlt_events",
            "--partition",
            config.partition,
        ),
        cwd=config.project_dir,
    )


def verify_rows(config: RunConfig) -> None:
    query = "SELECT count(*) FROM iceberg.raw.events"
    result = run(
        compose_command(config, "exec", "--no-TTY", "trino", "trino", "--execute", query),
        cwd=config.project_dir,
        capture_output=True,
    )
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    try:
        last_line = result.stdout.strip().splitlines()[-1].strip()
        if len(last_line) >= 2 and last_line[0] == last_line[-1] and last_line[0] in "'\"":
            last_line = last_line[1:-1].strip()
        if not last_line.isdigit():
            raise ValueError(last_line)
        count = int(last_line)
    except (IndexError, ValueError) as exc:
        raise RuntimeError(f"Trino returned no row count: {result.stdout!r}") from exc
    if count <= 0:
        raise RuntimeError(f"raw.events has no rows for partition {config.partition}")


def cleanup(
    config: RunConfig,
    *,
    owned_paths: set[Path],
    temporary_root: Path | None = None,
) -> list[Exception]:
    errors: list[Exception] = []
    if config.compose_file.exists():
        try:
            run(compose_command(config, "stop"), cwd=config.project_dir)
        except Exception as exc:
            errors.append(exc)
        try:
            run(
                compose_command(
                    config,
                    "run",
                    "--rm",
                    "--no-deps",
                    "--user",
                    "root",
                    "dagster",
                    "rm",
                    "-rf",
                    "/app/.venv",
                ),
                cwd=config.project_dir,
            )
        except Exception as exc:
            errors.append(exc)
        try:
            run(
                compose_command(config, "down", "--volumes", "--remove-orphans"),
                cwd=config.project_dir,
            )
        except Exception as exc:
            errors.append(exc)
    paths = set(owned_paths)
    if temporary_root:
        paths.add(temporary_root)
    for path in sorted(paths, key=lambda candidate: len(candidate.parts), reverse=True):
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        except Exception as exc:
            errors.append(exc)
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--keep-project", action="store_true")
    parser.add_argument("--partition", default=PARTITION)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    temporary_root: Path | None = None
    if args.project_dir:
        project_dir = args.project_dir.resolve()
        wheelhouse = project_dir.parent / "wheelhouse"
        operator_env = project_dir.parent / "operator-env"
        existing_paths = [path for path in (project_dir, wheelhouse, operator_env) if path.exists()]
        if existing_paths:
            print(
                "refusing to use existing project artifacts: "
                + ", ".join(str(path) for path in existing_paths),
                file=sys.stderr,
            )
            return 2
    else:
        temporary_root = Path(tempfile.mkdtemp(prefix=".phlo-release-golden-path-", dir=repo_root))
        project_dir = temporary_root / f"csv-batch-{os.getpid()}"
        wheelhouse = project_dir.parent / "wheelhouse"
        operator_env = project_dir.parent / "operator-env"
    owned_paths = {path for path in (project_dir, wheelhouse, operator_env) if not path.exists()}
    config = RunConfig(
        repo_root=repo_root,
        project_dir=project_dir,
        wheelhouse=wheelhouse,
        operator_env=operator_env,
        project_name=project_name(),
        partition=args.partition,
    )
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    primary_error: Exception | None = None
    cleanup_errors: list[Exception] = []
    try:
        build_wheelhouse(config)
        install_operator(config)
        create_project(config)
        align_project_name(config)
        install_project_dependencies(config)
        configure_non_dev_compose(config)
        start_stack(config)
        materialize_partition(config)
        verify_rows(config)
    except Exception as exc:
        primary_error = exc
    finally:
        if not args.keep_project:
            cleanup_errors = cleanup(
                config,
                owned_paths=owned_paths,
                temporary_root=temporary_root,
            )
        elif temporary_root:
            print(f"kept project at {project_dir}")

    if primary_error:
        print(f"release golden path failed: {primary_error}", file=sys.stderr)
    for error in cleanup_errors:
        print(f"release golden path cleanup failed: {error}", file=sys.stderr)
    if primary_error or cleanup_errors:
        return 1
    print("release golden path passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
