"""Select the active orchestrator adapter."""

from __future__ import annotations

from phlo.config import get_settings
from phlo.discovery import discover_plugins, get_global_registry
from phlo.exceptions import PhloConfigError
from phlo.logging import get_logger
from phlo.plugins.base import OrchestratorAdapterPlugin

logger = get_logger(__name__)


def get_active_orchestrator(name: str | None = None) -> OrchestratorAdapterPlugin:
    """Return the configured orchestrator adapter."""
    settings = get_settings()
    orchestrator_name = (name or settings.phlo_orchestrator or "dagster").strip()

    discover_plugins(plugin_type="orchestrators", auto_register=True)
    registry = get_global_registry()
    adapter = registry.get_orchestrator(orchestrator_name)
    if adapter is None:
        if orchestrator_name == "dagster":
            fallback = _load_dagster_adapter()
            if fallback is not None:
                return fallback
        raise PhloConfigError(
            message=f"Orchestrator adapter '{orchestrator_name}' is not installed.",
            suggestions=[
                f"Install a package that provides '{orchestrator_name}'",
                "Set PHLO_ORCHESTRATOR to an installed adapter name",
            ],
        )
    return adapter


def _load_dagster_adapter() -> OrchestratorAdapterPlugin | None:
    """Fallback to in-repo Dagster adapter when entry points are unavailable."""
    try:
        from phlo_dagster.adapter import DagsterOrchestratorAdapter
    except Exception as exc:  # noqa: BLE001 - optional dependency
        logger.exception("Failed to import Dagster adapter fallback: %s", exc)
        return None
    return DagsterOrchestratorAdapter()
