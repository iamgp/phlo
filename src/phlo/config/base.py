from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration class with common settings for all config domains."""

    model_config = SettingsConfigDict(
        env_file=(".phlo/.env", ".phlo/.env.local"),
        case_sensitive=False,
        extra="ignore",
    )
