"""Backwards compatibility shim for cli._services.utils.

This module has been moved to cli.infrastructure.utils.
All imports are re-exported for backwards compatibility.
"""

from phlo.cli.infrastructure.utils import *  # noqa: F401, F403
from phlo.cli.infrastructure.utils import (
    _resolve_container_name,
    find_dagster_container,
    get_project_config,
    get_project_name,
    parse_env_file,
)

__all__ = [
    "_resolve_container_name",
    "find_dagster_container",
    "get_project_config",
    "get_project_name",
    "parse_env_file",
]
