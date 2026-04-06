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
from phlo.config.network import resolve_host, resolve_url
from phlo.config.settings import Settings, _get_config, get_settings

__all__ = [
    "BaseConfig",
    "Settings",
    "_get_config",
    "get_settings",
    "resolve_host",
    "resolve_url",
]
