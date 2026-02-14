from functools import lru_cache

from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class Settings(BaseConfig):
    """Core configuration for Phlo."""

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
    """
    Get cached config instance.

    Uses lru_cache to ensure config is loaded once and reused.

    Returns:
        Validated Settings instance
    """
    return Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    This is the recommended way to access configuration in new code,
    as it's easier to test and allows for future dependency injection.

    Returns:
        Validated Settings instance
    """
    return _get_config()


config = _get_config()
