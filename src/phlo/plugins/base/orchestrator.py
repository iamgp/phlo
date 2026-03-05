"""
Orchestrator adapter plugin classes.

This module defines plugin types for orchestrator integration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec
from phlo.plugins.base.plugin import Plugin


class OrchestratorAdapterPlugin(Plugin, ABC):
    """Base class for orchestrator adapters."""

    @abstractmethod
    def build_definitions(
        self,
        *,
        assets: Iterable[AssetSpec],
        checks: Iterable[AssetCheckSpec],
        resources: Iterable[ResourceSpec],
    ) -> Any:
        """Build orchestrator definitions from normalized capability specs.

        Args:
            assets: Asset specifications to register.
            checks: Asset-check specifications to register.
            resources: Resource specifications required by assets/checks.

        Returns:
            Orchestrator-native definitions object.
        """
        raise NotImplementedError
