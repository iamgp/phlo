"""dbt project discovery for auto-wiring."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Common locations to search for dbt projects
DEFAULT_SEARCH_PATHS = [
    "transforms/dbt",
    "transforms",
    "dbt",
    ".",
]


def find_dbt_projects(
    root_dir: str | Path | None = None,
    search_paths: list[str] | None = None,
) -> list[Path]:
    """
    Discover dbt projects in the workspace.

    Args:
        root_dir: Root directory to search from. Defaults to current directory.
        search_paths: List of relative paths to search. Defaults to common locations.

    Returns:
        List of paths to discovered dbt_project.yml files
    """
    if root_dir is None:
        root_dir = Path.cwd()
    else:
        root_dir = Path(root_dir)

    if search_paths is None:
        search_paths = DEFAULT_SEARCH_PATHS

    discovered = []

    for search_path in search_paths:
        candidate = root_dir / search_path / "dbt_project.yml"
        if candidate.exists():
            discovered.append(candidate.parent)
            logger.info("Discovered dbt project: %s", candidate.parent)

    # Also search all immediate subdirectories for dbt_project.yml
    if root_dir.exists():
        for subdir in root_dir.iterdir():
            if subdir.is_dir() and (subdir / "dbt_project.yml").exists():
                if subdir not in discovered:
                    discovered.append(subdir)
                    logger.info("Discovered dbt project: %s", subdir)

    return discovered


def get_dbt_project_dir() -> Path:
    """
    Get the dbt project directory, auto-discovering if not explicitly set.

    Priority:
    1. DBT_PROJECT_DIR environment variable
    2. Auto-discovered project in workspace
    3. Default: transforms/dbt

    Returns:
        Path to dbt project directory
    """
    # Check explicit environment variable
    env_path = os.environ.get("DBT_PROJECT_DIR")
    if env_path:
        return Path(env_path)

    # Auto-discover
    projects = find_dbt_projects()
    if projects:
        return projects[0]

    # Fall back to default
    return Path("transforms/dbt")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    projects = find_dbt_projects()
    print(f"Discovered {len(projects)} dbt projects:")
    for p in projects:
        print(f"  - {p}")
