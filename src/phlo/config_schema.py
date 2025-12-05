"""
Infrastructure Configuration Schema

Pydantic models for phlo.yaml infrastructure section.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ServiceConfig(BaseModel):
    """Configuration for a single service."""

    container_name: Optional[str] = Field(
        default=None,
        description="Explicit container name override. If None, uses container_naming_pattern.",
    )
    service_name: str = Field(
        description="Docker compose service name (e.g., 'dagster-webserver', 'postgres')"
    )
    host: Optional[str] = Field(
        default="localhost",
        description="External hostname for accessing the service",
    )
    internal_host: Optional[str] = Field(
        default=None,
        description="Internal Docker network hostname. If None, uses service_name.",
    )

    @field_validator("container_name")
    @classmethod
    def validate_container_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        if not v:
            raise ValueError("container_name cannot be empty string")

        valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
        if not all(c in valid_chars for c in v.lower()):
            raise ValueError(
                "container_name must contain only alphanumeric characters, hyphens, underscores, and dots"
            )

        if v.startswith(("-", ".")):
            raise ValueError("container_name cannot start with hyphen or dot")

        return v

    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("service_name cannot be empty")
        return v.strip()

    def get_container_name(self, project_name: str, pattern: str) -> str:
        """Get effective container name, applying pattern if needed."""
        if self.container_name:
            return self.container_name
        return pattern.format(project=project_name, service=self.service_name)

    def get_internal_host(self) -> str:
        """Get effective internal hostname."""
        return self.internal_host or self.service_name


class NetworkConfig(BaseModel):
    """Docker network configuration."""

    name: Optional[str] = Field(
        default=None,
        description="Network name. If None, uses docker compose default.",
    )
    driver: str = Field(
        default="bridge",
        description="Network driver (e.g., 'bridge', 'overlay')",
    )


class InfrastructureConfig(BaseModel):
    """Infrastructure configuration section from phlo.yaml."""

    container_naming_pattern: str = Field(
        default="{project}-{service}-1",
        description="Pattern for generating container names. Available variables: {project}, {service}",
    )

    services: dict[str, ServiceConfig] = Field(
        default_factory=dict,
        description="Service definitions keyed by service identifier",
    )

    network: NetworkConfig = Field(
        default_factory=NetworkConfig,
        description="Docker network configuration",
    )

    @field_validator("container_naming_pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        if "{project}" not in v and "{service}" not in v:
            raise ValueError(
                "container_naming_pattern must contain at least {project} or {service}"
            )
        return v

    def get_service(self, service_key: str) -> Optional[ServiceConfig]:
        """Get service configuration by key."""
        return self.services.get(service_key)

    def get_container_name(self, service_key: str, project_name: str) -> Optional[str]:
        """Get container name for a service."""
        service = self.get_service(service_key)
        if not service:
            return None
        return service.get_container_name(project_name, self.container_naming_pattern)


def get_default_infrastructure_config() -> InfrastructureConfig:
    """Get default infrastructure configuration with all standard services."""
    return InfrastructureConfig(
        container_naming_pattern="{project}-{service}-1",
        services={
            "dagster_webserver": ServiceConfig(
                service_name="dagster-webserver",
                host="localhost",
                internal_host="dagster-webserver",
            ),
            "dagster_daemon": ServiceConfig(
                service_name="dagster-daemon",
                internal_host="dagster-daemon",
            ),
            "postgres": ServiceConfig(
                service_name="postgres",
                host="localhost",
                internal_host="postgres",
            ),
            "minio": ServiceConfig(
                service_name="minio",
                host="localhost",
                internal_host="minio",
            ),
            "nessie": ServiceConfig(
                service_name="nessie",
                host="localhost",
                internal_host="nessie",
            ),
            "trino": ServiceConfig(
                service_name="trino",
                host="localhost",
                internal_host="trino",
            ),
            "superset": ServiceConfig(
                service_name="superset",
                host="localhost",
                internal_host="superset",
            ),
            "postgrest": ServiceConfig(
                service_name="postgrest",
                host="localhost",
                internal_host="postgrest",
            ),
            "hasura": ServiceConfig(
                service_name="hasura",
                host="localhost",
                internal_host="hasura",
            ),
        },
    )
