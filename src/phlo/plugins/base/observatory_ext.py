"""
Observatory extension plugin classes.

This module defines plugin types for extending the Observatory UI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from importlib.resources.abc import Traversable
from typing import Any

from phlo.plugins.base.plugin import Plugin
from phlo.plugins.observatory import ObservatoryExtensionManifest


class ObservatoryExtensionPlugin(Plugin, ABC):
    """
    Base class for Observatory UI extension plugins.

    Extensions provide a manifest and a static asset root that the Observatory UI can load
    at runtime.
    """

    @property
    @abstractmethod
    def manifest(self) -> ObservatoryExtensionManifest | dict[str, Any]:
        """Return the extension manifest or a raw manifest dict."""
        raise NotImplementedError

    @property
    @abstractmethod
    def asset_root(self) -> Traversable:
        """Return the root directory that contains the extension assets."""
        raise NotImplementedError

    def get_manifest(self) -> ObservatoryExtensionManifest:
        """Return a validated manifest instance."""
        if isinstance(self.manifest, ObservatoryExtensionManifest):
            return self.manifest
        return ObservatoryExtensionManifest.model_validate(self.manifest)
