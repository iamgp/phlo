"""Phlo configuration module.

This module provides centralized configuration management for the Phlo framework.
It exports configuration classes and utilities for settings management, network
resolution, and base configuration patterns.

Key Components:
    - :class:`~phlo.config.base.BaseConfig`: Foundation for all config classes
    - :class:`~phlo.config.settings.Settings`: Primary application settings
    - :func:`~phlo.config.settings.get_settings`: Access cached settings
    - :func:`~phlo.config.network.resolve_host`: DNS resolution with fallback
    - :func:`~phlo.config.network.resolve_url`: URL resolution with fallback

Example:
    ```python
    from phlo.config import get_settings, Settings

    # Access settings
    settings = get_settings()
    print(settings.phlo_log_level)

    # Use in custom configuration
    class MyConfig(BaseConfig):
        my_setting: str = "default"
    ```

"""

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached
from phlo.config.env import (
    load_project_env,
    parse_project_env_file,
    project_env_files,
    project_env_value,
    resolve_project_root,
    use_project_root,
)
from phlo.config.network import resolve_host, resolve_url
from phlo.config.settings import Settings, _get_config, get_settings
from phlo.config.workflow import WorkflowSettingsError, settings, workflow_settings

__all__ = [
    "BaseConfig",
    "Settings",
    "WorkflowSettingsError",
    "_get_config",
    "get_settings",
    "load_project_env",
    "parse_project_env_file",
    "project_root_cached",
    "project_env_files",
    "project_env_value",
    "resolve_project_root",
    "resolve_host",
    "resolve_url",
    "settings",
    "use_project_root",
    "workflow_settings",
]
