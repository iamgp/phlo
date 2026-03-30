"""Base configuration classes for Phlo.

This module provides the foundational configuration infrastructure used across
all Phlo components. It defines the base configuration class with common
settings for environment variable loading and validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration class with common settings for all config domains.

    This class provides a standardized foundation for all Phlo configuration
    classes. It handles environment variable loading from `.phlo/.env` and
    `.phlo/.env.local` files with case-insensitive matching.

    Attributes:
        model_config: Pydantic settings configuration with env file paths,
            case-insensitive matching, and extra field ignoring.

    Example:
        ```python
        from phlo.config.base import BaseConfig
        from pydantic import Field

        class DatabaseConfig(BaseConfig):
            postgres_host: str = Field(default="localhost")
            postgres_port: int = Field(default=5432)
        ```

    """

    model_config = SettingsConfigDict(
        env_file=(".phlo/.env", ".phlo/.env.local"),
        case_sensitive=False,
        extra="ignore",
    )
