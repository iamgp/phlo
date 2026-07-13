"""Settings for phlo-dlt package.

This module provides configuration management for the phlo-dlt package
using Pydantic settings. It defines default values and allows customization
via environment variables or configuration files.

Key Components:
    - :class:`DltSettings`: Pydantic settings class for DLT configuration
    - :func:`get_settings`: Cached factory for settings instance

Configuration Options:
    - dlt_default_namespace: Default schema/namespace for table names

Environment Variables:
    Settings can be configured via environment variables with the prefix
    ``PHLO_DLT_`` (e.g., ``PHLO_DLT_DEFAULT_NAMESPACE``).

See Also:
    - :mod:`phlo.config.base`: Base configuration class
    - :mod:`phlo_dlt.registry`: Uses settings for namespace resolution
    - Pydantic Settings: https://docs.pydantic.dev/latest/concepts/settings/

Example:
    ```python
    from phlo_dlt.settings import get_settings

    settings = get_settings()
    print(settings.dlt_default_namespace)  # "raw"
    ```

"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from phlo.config.base import BaseConfig
from phlo.config.cache import project_root_cached


class DltSettings(BaseConfig):
    """Configuration for DLT ingestion defaults.

    Pydantic-based settings class that provides default configuration
    values for DLT ingestion operations. Values can be overridden via
    environment variables or .env files.

    Attributes:
        dlt_default_namespace: Default namespace/schema used for generated
            ingestion table names. Prepended to table_name to create
            full_table_name.

    Environment:
        Set ``PHLO_DLT_DEFAULT_NAMESPACE`` to override the default namespace.

    Example:
        ```python
        from phlo_dlt.settings import DltSettings

        # Default namespace is "raw"
        settings = DltSettings()
        print(settings.dlt_default_namespace)  # "raw"

        # Override via environment
        import os
        os.environ["PHLO_DLT_DEFAULT_NAMESPACE"] = "staging"
        settings = DltSettings()
        print(settings.dlt_default_namespace)  # "staging"
        ```

    """

    dlt_default_namespace: str = Field(
        default="raw",
        description="Default namespace/schema used for generated ingestion table names.",
    )


@project_root_cached
def get_settings(project_root: Path) -> DltSettings:
    """Return cached DLT settings instance.

    Factory function that returns a singleton DltSettings instance.
    Uses functools.lru_cache to ensure only one settings object is created
    per process, improving performance and ensuring consistency.

    Returns:
        DltSettings: The cached settings instance.

    Example:
        ```python
        from phlo_dlt.settings import get_settings

        # First call creates the instance
        settings = get_settings()

        # Subsequent calls return the same instance
        settings2 = get_settings()
        assert settings is settings2  # True
        ```

    """
    return DltSettings()
