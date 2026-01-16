"""
Catalog plugin classes.

This module defines plugin types for catalog configuration.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any

from phlo.plugins.base.plugin import Plugin


class CatalogPlugin(Plugin, ABC):
    """
    Base class for engine-agnostic catalog plugins.

    Catalog plugins define logical catalog configuration that engine adapters
    serialize into their native formats (files or programmatic config).

    Example:
        ```python
        class IcebergCatalogPlugin(CatalogPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="iceberg",
                    version="1.0.0",
                    description="Iceberg catalog with Nessie backend",
                )

            @property
            def targets(self) -> list[str]:
                return ["trino", "spark"]

            @property
            def catalog_name(self) -> str:
                return "iceberg"

            def get_properties(self) -> dict[str, str]:
                return {
                    "connector.name": "iceberg",
                    "iceberg.catalog.type": "rest",
                    "iceberg.rest-catalog.uri": "http://nessie:19120/iceberg",
                }
        ```
    """

    @property
    @abstractmethod
    def targets(self) -> list[str]:
        """
        Return engine identifiers that can consume this catalog.

        Examples: ["trino"], ["spark"], ["trino", "spark"].
        """
        pass

    @property
    @abstractmethod
    def catalog_name(self) -> str:
        """
        Return the catalog name.

        This becomes the catalog identifier in the engine.
        """
        pass

    @abstractmethod
    def get_properties(self) -> dict[str, Any]:
        """
        Return catalog configuration as key-value pairs.

        Returns:
            Dictionary of config key -> value
        """
        pass

    def supports_target(self, target: str) -> bool:
        """Return True if the catalog supports the requested engine target."""
        return target in self.targets


class TrinoCatalogPlugin(CatalogPlugin, ABC):
    """
    Deprecated: use CatalogPlugin with targets=["trino"] instead.
    """

    def __init__(self) -> None:
        warnings.warn(
            "TrinoCatalogPlugin is deprecated; use CatalogPlugin with targets=['trino'].",
            DeprecationWarning,
            stacklevel=2,
        )

    @property
    def targets(self) -> list[str]:
        return ["trino"]
