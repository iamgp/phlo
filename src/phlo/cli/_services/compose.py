from __future__ import annotations

from pathlib import Path
from typing import Iterable


def compose_base_cmd(
    *,
    phlo_dir: Path,
    project_name: str,
    profiles: Iterable[str] = (),
) -> list[str]:
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"

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

    project_env = Path.cwd() / ".env"
    if project_env.exists():
        cmd.extend(["--env-file", str(project_env)])

    for profile in profiles:
        cmd.extend(["--profile", profile])

    return cmd
