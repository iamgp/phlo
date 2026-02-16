"""Dagster settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator

from phlo.config.base import BaseConfig


class DagsterSettings(BaseConfig):
    """Dagster orchestration configuration."""

    dagster_port: int = Field(default=10006, description="Dagster webserver port")
    workflows_path: str = Field(
        default="workflows",
        description="Path to user workflows directory (for external projects)",
    )
    phlo_force_in_process_executor: bool = Field(
        default=False, description="Force use of in-process executor"
    )
    phlo_force_multiprocess_executor: bool = Field(
        default=False, description="Force use of multiprocess executor"
    )
    phlo_host_platform: str | None = Field(
        default=None,
        description="Host platform for executor selection (Darwin/Linux/Windows). "
        "Auto-detected in CLI; set explicitly for daemon/webserver on macOS.",
    )

    @model_validator(mode="after")
    def validate_executor_flags(self) -> "DagsterSettings":
        """Validate mutually exclusive executor override flags.

        Returns:
            Validated settings instance.

        Raises:
            ValueError: If both force flags are set simultaneously.
        """
        if self.phlo_force_in_process_executor and self.phlo_force_multiprocess_executor:
            raise ValueError(
                "phlo_force_in_process_executor and phlo_force_multiprocess_executor "
                "cannot both be True"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> DagsterSettings:
    """Return cached Dagster settings."""
    return DagsterSettings()
