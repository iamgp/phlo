from pydantic import AliasChoices, Field

from phlo.config.base import BaseConfig


class OrchestrationConfig(BaseConfig):
    """Dagster data orchestration platform configuration."""

    dagster_port: int = Field(default=10006, description="Dagster webserver port")
    phlo_orchestrator: str = Field(
        default="dagster",
        validation_alias=AliasChoices("PHLO_ORCHESTRATOR", "PHLO_ORCHESTRATOR_NAME"),
        description="Active orchestrator adapter name",
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

    app_port: int = Field(default=10009, description="Hub application port")
    flask_debug: bool = Field(default=False, description="Flask debug mode")
