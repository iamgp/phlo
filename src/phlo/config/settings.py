"""Core application settings for Phlo.

This module defines the primary configuration settings used throughout the Phlo
framework. Settings are loaded from environment variables and `.phlo/.env` files
with validation via Pydantic.

All settings can be customized through environment variables or by creating
a `.phlo/.env` file in your project root.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class Settings(BaseConfig):
    """Core configuration for Phlo.

    This class defines all configurable aspects of the Phlo framework including
    logging, orchestration, plugin management, and observability settings.
    Values are loaded from environment variables with sensible defaults.

    Environment variables are read with case-insensitive matching. Aliases
    are provided for common configuration patterns (e.g., OTEL_* variables).

    Attributes:
        phlo_orchestrator: Active orchestrator adapter name (default: "dagster").
        phlo_log_level: Default log level (default: "INFO").
        phlo_log_format: Log output format - "auto", "json", or "console".
        phlo_log_router_enabled: Enable structured log event routing to hook bus.
        phlo_log_service_name: Default service name for log records.
        phlo_log_file_template: Optional log file path template with date placeholders.
        phlo_environment: Runtime environment identifier (dev, staging, prod).
        phlo_service_namespace: Service namespace for observability resources.
        phlo_service_version: Optional service version for observability.
        phlo_service_instance_id: Optional instance identifier for observability.
        phlo_project: Optional project identifier for observability.
        phlo_default_capabilities: Default capability provider mappings.
        plugins_enabled: Enable the plugin system.
        plugins_auto_discover: Automatically discover plugins from entry points.
        plugins_whitelist: List of allowed plugin names (empty = all allowed).
        plugins_blacklist: List of plugin names to exclude.
        plugin_registry_url: URL for the plugin registry catalog.
        plugin_registry_cache_ttl_seconds: Cache TTL for registry responses.
        plugin_registry_timeout_seconds: Timeout for registry fetch requests.

    Example:
        ```python
        from phlo.config import get_settings

        settings = get_settings()
        print(f"Orchestrator: {settings.phlo_orchestrator}")
        print(f"Log level: {settings.phlo_log_level}")
        ```

    """

    phlo_orchestrator: str = Field(
        default="dagster",
        validation_alias=AliasChoices("PHLO_ORCHESTRATOR", "PHLO_ORCHESTRATOR_NAME"),
        description="Active orchestrator adapter name",
    )

    phlo_log_level: str = Field(default="INFO", description="Default log level for Phlo")
    phlo_log_format: str = Field(
        default="auto",
        description="Log format (auto|json|console)",
    )
    phlo_log_router_enabled: bool = Field(
        default=True,
        description="Emit structured log events to the hook bus",
    )
    phlo_log_service_name: str = Field(
        default="phlo",
        description="Default service name for log records",
    )
    phlo_log_file_template: str = Field(
        default=".phlo/logs/{YMD}.log",
        description="Optional log file path template (empty to disable)",
    )
    phlo_environment: str = Field(
        default="dev",
        validation_alias=AliasChoices("PHLO_ENVIRONMENT", "ENVIRONMENT"),
        description="Runtime environment attached to structured logs",
    )
    phlo_service_namespace: str = Field(
        default="phlo",
        validation_alias=AliasChoices("PHLO_SERVICE_NAMESPACE", "OTEL_SERVICE_NAMESPACE"),
        description="Default service namespace attached to observability resources",
    )
    phlo_service_version: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_SERVICE_VERSION", "OTEL_SERVICE_VERSION"),
        description="Optional default service version attached to observability resources",
    )
    phlo_service_instance_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_SERVICE_INSTANCE_ID", "OTEL_SERVICE_INSTANCE_ID"),
        description="Optional default service instance identifier for observability resources",
    )
    phlo_project: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PHLO_PROJECT"),
        description="Optional project identifier attached to observability resources",
    )
    phlo_default_capabilities: dict[str, str] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("PHLO_DEFAULT_CAPABILITIES"),
        description=(
            "Default capability provider names keyed by capability type "
            "(for example {'table_store': 'iceberg'})"
        ),
    )

    plugins_enabled: bool = Field(default=True, description="Enable plugin system")
    plugins_auto_discover: bool = Field(
        default=True,
        description="Automatically discover plugins from entry points on import",
    )
    plugins_whitelist: list[str] = Field(
        default_factory=list,
        description="Whitelist of plugin names to load (empty = all allowed)",
    )
    plugins_blacklist: list[str] = Field(
        default_factory=list, description="Blacklist of plugin names to exclude"
    )
    plugin_registry_url: str = Field(
        default="https://registry.phlohouse.com/plugins.json",
        description="URL for the plugin registry catalog",
    )
    plugin_registry_cache_ttl_seconds: int = Field(
        default=3600, description="Registry cache TTL in seconds"
    )
    plugin_registry_timeout_seconds: int = Field(
        default=10, description="Registry fetch timeout in seconds"
    )


@lru_cache
def _get_config() -> Settings:
    """Get cached config instance.

    Uses lru_cache to ensure config is loaded once and reused across
    the application lifecycle. This provides efficient access to settings
    without repeated file I/O or parsing.

    Returns:
        Settings: Validated Settings instance with all configuration values.

    Note:
        This is an internal function. Use :func:`get_settings` for public access.

    """
    return Settings()


def get_settings() -> Settings:
    """Get application settings.

    This is the recommended way to access configuration in application code.
    It returns a cached Settings instance and supports future dependency
    injection patterns for testing.

    Returns:
        Settings: Validated Settings instance with all configuration values.

    Example:
        ```python
        from phlo.config import get_settings

        settings = get_settings()
        if settings.phlo_environment == "production":
            # Apply production-specific logic
            pass
        ```

    """
    return _get_config()


config = _get_config()
# Global cached configuration instance.
# This module-level variable provides direct access to the cached settings
# for convenience. Prefer using :func:`get_settings` in new code for better
# testability.
