"""
Provider plugin classes.

This module defines plugin types that provide asset and resource specifications.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from phlo.capabilities.specs import AssetCheckSpec, AssetSpec, ResourceSpec
from phlo.plugins.base.plugin import Plugin


class AssetProviderPlugin(Plugin, ABC):
    """Base class for capability plugins that provide asset specs."""

    @abstractmethod
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return asset specifications exposed by this plugin.

        Returns:
            Iterable of asset specifications.
        """

        raise NotImplementedError

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset check specifications exposed by this plugin.

        Returns:
            Iterable of asset check specifications.
        """

        return []


class ResourceProviderPlugin(Plugin, ABC):
    """Base class for plugins that provide resource specs."""

    @abstractmethod
    def get_resources(self) -> Iterable[ResourceSpec]:
        """Return resource specifications exposed by this plugin.

        Returns:
            Iterable of resource specifications.
        """

        raise NotImplementedError
