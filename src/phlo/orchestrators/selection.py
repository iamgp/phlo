"""Select the active orchestrator adapter."""

from __future__ import annotations

from phlo.config import get_settings
from phlo.exceptions import PhloConfigError
from phlo.logging import get_logger
from phlo.plugins.base import OrchestratorAdapterPlugin
from phlo.plugins.discovery import discover_plugins, get_global_registry

logger = get_logger(__name__)


def get_active_orchestrator(name: str | None = None) -> OrchestratorAdapterPlugin:
    """Return the configured orchestrator adapter."""
    settings = get_settings()
    orchestrator_name = (name or settings.phlo_orchestrator or "dagster").strip()
    logger.debug("orchestrator_selection_started", requested_name=orchestrator_name)

    discover_plugins(plugin_type="orchestrators", auto_register=True)
    registry = get_global_registry()
    adapter = registry.get_orchestrator(orchestrator_name)
    if adapter is None:
        logger.warning(
            "orchestrator_not_installed",
            requested_name=orchestrator_name,
            available_orchestrators=registry.list_orchestrators(),
        )
        raise PhloConfigError(
            message=f"Orchestrator adapter '{orchestrator_name}' is not installed.",
            suggestions=[
                f"Install a package that provides '{orchestrator_name}'",
                "Set PHLO_ORCHESTRATOR to an installed adapter name",
            ],
        )
    logger.debug("orchestrator_selected", selected_name=orchestrator_name)
    return adapter
