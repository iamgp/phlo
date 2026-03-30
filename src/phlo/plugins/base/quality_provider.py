"""Quality provider plugin classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from phlo.plugins.base.plugin import Plugin

TQualityCheck = TypeVar("TQualityCheck")


class QualityProviderPlugin(Plugin, ABC):
    """Base class for quality provider plugins.

    Quality provider plugins supply the core quality primitives:
    - The @phlo_quality decorator
    - Built-in check classes (NullCheck, RangeCheck, etc.)
    - Schema extraction capabilities

    Example:
        ```python
        from phlo.plugins.base import QualityProviderPlugin, PluginMetadata

        class PanderaQualityProvider(QualityProviderPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="pandera",
                    version="0.1.0",
                    description="Pandera-based quality provider",
                )

            def get_decorator(self) -> Callable:
                from phlo_pandera import phlo_quality
                return phlo_quality

            def get_check_classes(self) -> dict[str, type]:
                from phlo_pandera import (
                    NullCheck, RangeCheck, FreshnessCheck,
                    UniqueCheck, CountCheck, SchemaCheck,
                )
                return {
                    "null": NullCheck,
                    "range": RangeCheck,
                    "freshness": FreshnessCheck,
                    "unique": UniqueCheck,
                    "count": CountCheck,
                    "schema": SchemaCheck,
                }

            def get_schema_extractor(self) -> Any:
                from phlo_pandera import PanderaSchemaExtractor
                return PanderaSchemaExtractor
        ```

    """

    @abstractmethod
    def get_decorator(self) -> Callable:
        """Return the quality decorator function.

        Returns:
            The @phlo_quality decorator or equivalent.

        Example:
            ```python
            def get_decorator(self) -> Callable:
                from phlo_pandera import phlo_quality
                return phlo_quality
            ```

        """

    @abstractmethod
    def get_check_classes(self) -> dict[str, type]:
        """Return a mapping of check type names to classes.

        Returns:
            Dictionary mapping short names to check classes.

        Example:
            ```python
            def get_check_classes(self) -> dict[str, type]:
                from phlo_pandera import NullCheck, RangeCheck
                return {"null": NullCheck, "range": RangeCheck}
            ```

        """

    def get_schema_extractor(self) -> Any | None:
        """Return a schema extractor class for converting native schemas.

        Returns:
            Schema extractor class, or None if not available.

        """
        return None

    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes.

        Returns:
            Dictionary mapping check names to classes, or None.

        """
        return None
