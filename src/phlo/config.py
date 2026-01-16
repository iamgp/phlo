"""Backwards-compatible shim for phlo.config.

This module re-exports all configuration classes from phlo.config/ for
backwards compatibility. New code should import from phlo.config directly.

Example (both work):
    # Old style (still works)
    from phlo.config import Settings, get_settings, config

    # New style (preferred)
    from phlo.config import Settings, get_settings
    from phlo.config.database import DatabaseConfig
"""

from phlo.config import (
    AlertingConfig,
    BaseConfig,
    CatalogConfig,
    DatabaseConfig,
    IntegrationConfig,
    ObservabilityConfig,
    OrchestrationConfig,
    QueryConfig,
    Settings,
    StorageConfig,
    config,
    get_settings,
)

__all__ = [
    "AlertingConfig",
    "BaseConfig",
    "CatalogConfig",
    "DatabaseConfig",
    "IntegrationConfig",
    "ObservabilityConfig",
    "OrchestrationConfig",
    "QueryConfig",
    "Settings",
    "StorageConfig",
    "config",
    "get_settings",
]
