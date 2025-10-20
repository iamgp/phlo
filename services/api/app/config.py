
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API service configuration."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # API Settings
    api_title: str = "Cascade Lakehouse API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # JWT Settings
    jwt_secret: str = "cascade-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # Hasura Settings (for shared JWT)
    hasura_graphql_jwt_secret: str = "cascade-jwt-secret-change-in-production"

    # Cache Settings (in-memory)
    cache_default_ttl: int = 3600  # 1 hour
    cache_glucose_readings_ttl: int = 3600  # 1 hour
    cache_hourly_patterns_ttl: int = 21600  # 6 hours
    cache_iceberg_queries_ttl: int = 1800  # 30 minutes

    # Rate Limiting
    rate_limit_admin: str = "1000/minute"
    rate_limit_analyst: str = "100/minute"
    rate_limit_default: str = "50/minute"

    # Query Limits
    max_query_rows: int = 10000
    query_timeout_seconds: int = 30

    # Trino Connection
    trino_host: str = "trino"
    trino_port: int = 10005
    trino_catalog: str = "iceberg"
    trino_user: str = "cascade"

    # Postgres Connection
    postgres_host: str = "postgres"
    postgres_port: int = 10000
    postgres_db: str = "lakehouse"
    postgres_user: str = "lake"
    postgres_password: str = "lakepass"

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
