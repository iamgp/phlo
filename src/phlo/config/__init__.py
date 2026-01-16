"""Phlo configuration module.

This module provides domain-specific configuration classes organized by concern:

- DatabaseConfig: PostgreSQL database settings
- StorageConfig: MinIO S3-compatible storage settings
- CatalogConfig: Nessie catalog and Iceberg settings
- QueryConfig: Trino query engine settings
- OrchestrationConfig: Dagster orchestration settings
- ObservabilityConfig: Logging and plugin settings
- AlertingConfig: Alert integration settings (Slack, PagerDuty, Email)
- IntegrationConfig: External service integrations (OpenMetadata, dbt, Superset)
- Settings: Unified configuration composing all domain configs

Usage:
    from phlo.config import get_settings, Settings

    settings = get_settings()
    print(settings.postgres_host)

For domain-specific imports:
    from phlo.config.database import DatabaseConfig
    from phlo.config.storage import StorageConfig
"""

from phlo.config.alerting import AlertingConfig
from phlo.config.base import BaseConfig
from phlo.config.catalog import CatalogConfig
from phlo.config.database import DatabaseConfig
from phlo.config.integration import IntegrationConfig
from phlo.config.observability import ObservabilityConfig
from phlo.config.orchestration import OrchestrationConfig
from phlo.config.query import QueryConfig
from phlo.config.settings import Settings, _get_config, config, get_settings
from phlo.config.storage import StorageConfig

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
    "_get_config",
    "config",
    "get_settings",
]
