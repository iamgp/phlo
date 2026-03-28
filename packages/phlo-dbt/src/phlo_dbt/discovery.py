"""dbt project discovery for auto-wiring.

This module provides utilities for automatically discovering dbt projects
within the workspace. It searches common locations and environment variables
to locate dbt_project.yml files, enabling zero-configuration setup in many cases.

Example:
    >>> from phlo_dbt.discovery import find_dbt_projects, get_dbt_project_dir
    >>>
    >>> # Find all dbt projects in workspace
    >>> projects = find_dbt_projects()
    >>> for project in projects:
    ...     print(f"Found: {project}")
    >>>
    >>> # Get the primary project directory
    >>> project_dir = get_dbt_project_dir()
    >>> print(f"Using: {project_dir}")

"""

from __future__ import annotations

import os
from pathlib import Path

from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Common locations to search for dbt projects
DEFAULT_SEARCH_PATHS = [
    "workflows/transforms/dbt",
]


def find_dbt_projects(
    root_dir: str | Path | None = None,
    search_paths: list[str] | None = None,
) -> list[Path]:
    """Discover dbt projects in the workspace.

    Searches for dbt_project.yml files in specified paths relative to the root
    directory. Returns paths to directories containing valid dbt projects.

    Args:
        root_dir: Root directory to search from. Defaults to current working directory.
        search_paths: List of relative paths to search. Defaults to DEFAULT_SEARCH_PATHS.

    Returns:
        List of paths to discovered dbt project directories (parent directories
        of dbt_project.yml files).

    Example:
        >>> # Find projects in default locations
        >>> projects = find_dbt_projects()
        >>> print(projects)
        [PosixPath('workflows/transforms/dbt')]
        >>>
        >>> # Search custom locations
        >>> projects = find_dbt_projects(
        ...     root_dir="/custom/path",
        ...     search_paths=["analytics/dbt", "data/transforms"]
        ... )

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

    return discovered


def get_dbt_project_dir() -> Path:
    """Get the dbt project directory, auto-discovering if not explicitly set.

    Resolves the dbt project directory using a priority system:
    1. DBT_PROJECT_DIR environment variable
    2. Auto-discovered project in workspace
    3. Default: workflows/transforms/dbt

    Returns:
        Path to dbt project directory. May not exist if falling back to default
        and project hasn't been scaffolded yet.

    Example:
        >>> # With environment variable set
        >>> import os
        >>> os.environ["DBT_PROJECT_DIR"] = "/custom/dbt"
        >>> project_dir = get_dbt_project_dir()
        >>> print(project_dir)
        PosixPath('/custom/dbt')
        >>>
        >>> # With auto-discovery
        >>> project_dir = get_dbt_project_dir()
        >>> # Returns first discovered project or default path

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
    return Path("workflows/transforms/dbt")


if __name__ == "__main__":
    setup_logging()
    projects = find_dbt_projects()
    logger.info("Discovered %s dbt projects:", len(projects))
    for project in projects:
        logger.info("  - %s", project)
