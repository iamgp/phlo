"""
Phlo Services Management (Compatibility Shim)

This module now exports from the refactored commands structure.
All command implementations are in phlo.cli.commands.services/.
"""

# Re-export the main services group
from phlo.cli.commands.services import services_group as services

# Re-export constants for backwards compatibility
from phlo.cli.commands.services.utils import (
    NATIVE_STATE_FILE,
    PHLO_CONFIG_FILE,
    PHLO_CONFIG_TEMPLATE,
    check_docker_running,
    detect_phlo_source_path,
    ensure_phlo_dir,
    get_phlo_dir,
    get_profile_service_names,
    relpath_from_phlo_dir,
    require_docker,
    resolve_phlo_package_dir,
)

# Re-export from utils for backwards compatibility
from phlo.cli.infrastructure.utils import (
    find_dagster_container,
    get_project_config,
    get_project_name,
    parse_env_file,
)

__all__ = [
    "services",
    "PHLO_CONFIG_FILE",
    "PHLO_CONFIG_TEMPLATE",
    "NATIVE_STATE_FILE",
    "get_phlo_dir",
    "ensure_phlo_dir",
    "check_docker_running",
    "require_docker",
    "detect_phlo_source_path",
    "resolve_phlo_package_dir",
    "relpath_from_phlo_dir",
    "get_profile_service_names",
    "get_project_config",
    "get_project_name",
    "find_dagster_container",
    "parse_env_file",
]
