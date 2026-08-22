"""Build docker/podman compose commands for a Phlo project's selected backend."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from phlo.cli.infrastructure.container_backend import select_project_container_backend


def compose_base_cmd(
    *,
    phlo_dir: Path,
    project_name: str,
    profiles: Iterable[str] = (),
    backend_name: str | None = None,
) -> list[str]:
    """Build the base compose command for a Phlo project.

    Args:
        phlo_dir: Directory containing compose and environment files.
        project_name: Compose project name.
        profiles: Optional compose profile names to enable.
        backend_name: Optional container backend override.

    Returns:
        Base command tokens for compose invocation.
    """
    backend = select_project_container_backend(cli_backend=backend_name)
    return backend.compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name=project_name,
        profiles=tuple(profiles),
    )
