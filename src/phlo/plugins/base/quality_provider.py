"""Quality provider plugin classes.

QualityProviderPlugin is the abstract extension point for quality engines:
it supplies the check decorator, check classes, schema extraction, and schema
module rendering used when scaffolding typed quality schemas.
"""

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

    def get_schema_base_import(self) -> tuple[str, str] | None:
        """Return the schema base import for generated project schemas.

        Returns:
            Tuple of (module, symbol), or None if this provider does not expose
            a generated-schema base class.

        """
        return None

    def render_schema_field(
        self,
        *,
        name: str,
        type_name: str,
        nullable: bool,
        description: str | None = None,
    ) -> str | None:
        """Render one generated schema field for this quality provider.

        Returns:
            Python source for a class-level field declaration, or None when the
            provider does not support schema scaffolding.

        """
        return None

    def render_schema_module(
        self,
        *,
        domain: str,
        schema_class: str,
        type_imports: str,
        schema_fields: str,
    ) -> str | None:
        """Render a complete generated schema module for this quality provider.

        Returns:
            Python source for the schema module, or None when the provider does
            not support schema scaffolding.

        """
        return None

    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes.

        Returns:
            Dictionary mapping check names to classes, or None.

        """
        return None

    def build_checks_from_rules(self, rules: list[Any]) -> list[Any] | None:
        """Translate provider-neutral quality rules into provider-native checks.

        Returning None means this provider does not support neutral rule
        translation.
        """
        return None
