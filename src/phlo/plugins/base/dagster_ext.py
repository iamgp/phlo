"""
Dagster extension plugin classes.

This module defines plugin types that extend Dagster functionality.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

from phlo.plugins.base.plugin import Plugin


class DagsterExtensionPlugin(Plugin, ABC):
    """
    Base class for Dagster extension plugins.

    These plugins contribute Dagster definitions (assets/resources/schedules/sensors/etc.)
    to the running Phlo instance.
    """

    def get_definitions(self) -> Any:
        """Return Dagster definitions to merge into the global Definitions."""
        try:
            import dagster as dg
        except Exception as exc:  # noqa: BLE001 - optional dependency
            raise RuntimeError("Dagster is required for DagsterExtensionPlugin") from exc
        return dg.Definitions()

    def get_exports(self) -> dict[str, Any]:
        """
        Return exported symbols to attach to the `phlo` public API.

        Example: {"ingestion": phlo_ingestion}
        """
        return {}

    def clear_registries(self) -> None:
        """
        Clear any global registries used by this plugin (primarily for module reload and tests).
        """
        ...


class IngestionEnginePlugin(DagsterExtensionPlugin, ABC):
    """
    Base class for ingestion engine capability plugins.

    Deprecated in favor of capability specs + orchestrator adapters.
    """

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            "IngestionEnginePlugin is deprecated; use capability specs instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    def get_ingestion_assets(self) -> Iterable[Any]:
        """Return Dagster assets created by the ingestion engine."""
        ...

    @abstractmethod
    def get_ingestion_decorator(self) -> Callable[..., Any]:
        """Return the decorator used to define ingestion assets."""
        ...
