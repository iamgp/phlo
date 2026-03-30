"""Pandera quality provider plugin.

This module implements the PanderaQualityProvider plugin class that integrates
the Phlo Quality Framework with Phlo's plugin system. The provider exposes:

1. **Decorator**: The ``@phlo_pandera`` decorator for declarative quality checks
2. **Check Classes**: All built-in quality check implementations
3. **Schema Extractor**: PanderaSchemaExtractor for schema normalization
4. **Reconciliation Checks**: Cross-table validation checks

The plugin is registered via the ``phlo.quality_providers`` entry point and is
discovered automatically by Phlo's plugin system.

Example:
    The plugin is typically not used directly. Instead, users interact with
    the public API from ``phlo_pandera``:

    ```python
    from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

    @phlo_pandera(
        table="bronze.events",
        checks=[
            NullCheck(columns=["event_id"]),
            RangeCheck(column="value", min_value=0, max_value=100),
        ],
    )
    def event_quality():
        pass
    ```

Plugin Registration:
    The plugin is registered in ``pyproject.toml``:

    ```toml
    [project.entry-points."phlo.quality_providers"]
    pandera = "phlo_pandera.plugin:PanderaQualityProvider"
    ```

See Also:
    - ``__init__.py``: Public API exports
    - ``decorator.py``: ``@phlo_pandera`` implementation
    - ``checks.py``: Core quality check classes
    - ``reconciliation.py``: Cross-table reconciliation checks

"""

from __future__ import annotations

from typing import Any, Callable

from phlo.plugins.base import PluginMetadata, QualityProviderPlugin


class PanderaQualityProvider(QualityProviderPlugin):
    """Pandera-based quality provider for Phlo.

    This plugin class integrates the Phlo Quality Framework with Phlo's plugin
    system. It provides access to all quality check classes, the ``@phlo_pandera``
    decorator, schema extraction, and reconciliation checks.

    The plugin is automatically discovered by Phlo's plugin system via the
    ``phlo.quality_providers`` entry point.

    Attributes:
        metadata: Plugin identification information (name, version, description).

    Example:
        The plugin is typically accessed through the plugin system:

        ```python
        from phlo.plugins import get_plugin_registry

        registry = get_plugin_registry()
        quality_plugins = registry.get_quality_providers()
        pandera_plugin = quality_plugins.get("pandera")

        # Access decorator
        decorator = pandera_plugin.get_decorator()

        # Get check classes
        checks = pandera_plugin.get_check_classes()
        null_check_class = checks.get("null")
        ```

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Provides identification information used during plugin registration
        and discovery.

        Returns:
            PluginMetadata with name="pandera", version, and description.

        """
        return PluginMetadata(
            name="pandera",
            version="0.1.0",
            description="Pandera-based quality provider with schema validation and checks",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_pandera decorator.

        Returns the main decorator used for defining quality checks in a
        declarative manner.

        Returns:
            The ``phlo_pandera`` decorator function.

        Example:
            ```python
            provider = PanderaQualityProvider()
            phlo_pandera = provider.get_decorator()

            @phlo_pandera(table="bronze.events", checks=[...])
            def quality_check():
                pass
            ```

        """
        from phlo_pandera import phlo_pandera

        return phlo_pandera

    def get_check_classes(self) -> dict[str, type]:
        """Return built-in check classes.

        Returns a dictionary mapping check type names to their corresponding
        class implementations.

        Returns:
            Dictionary of check class names to types, including:
            - null, range, freshness, unique, count
            - schema, pattern, quality_check (base class)

        Example:
            ```python
            provider = PanderaQualityProvider()
            checks = provider.get_check_classes()

            NullCheck = checks["null"]
            RangeCheck = checks["range"]
            ```

        """
        from phlo_pandera import (
            CountCheck,
            FreshnessCheck,
            NullCheck,
            PatternCheck,
            QualityCheck,
            RangeCheck,
            SchemaCheck,
            UniqueCheck,
        )

        return {
            "null": NullCheck,
            "range": RangeCheck,
            "freshness": FreshnessCheck,
            "unique": UniqueCheck,
            "count": CountCheck,
            "schema": SchemaCheck,
            "pattern": PatternCheck,
            "quality_check": QualityCheck,
        }

    def get_schema_extractor(self) -> Any:
        """Return Pandera schema extractor.

        Returns the schema extractor class used to convert Pandera DataFrameModel
        schemas into normalized schemas for storage provider integration.

        Returns:
            PanderaSchemaExtractor class (not an instance).

        Example:
            ```python
            provider = PanderaQualityProvider()
            Extractor = provider.get_schema_extractor()

            extractor = Extractor()
            normalized_schema = extractor.extract(MyPanderaSchema)
            ```

        """
        from phlo_pandera import PanderaSchemaExtractor

        return PanderaSchemaExtractor

    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes.

        Returns a dictionary mapping reconciliation check type names to their
        corresponding class implementations. These checks validate data
        consistency across tables.

        Returns:
            Dictionary of reconciliation check names to types, including:
            - reconciliation (row count parity)
            - aggregate_consistency
            - key_parity
            - multi_aggregate
            - checksum

        Example:
            ```python
            provider = PanderaQualityProvider()
            reconciliations = provider.get_reconciliation_checks()

            ReconciliationCheck = reconciliations["reconciliation"]
            KeyParityCheck = reconciliations["key_parity"]
            ```

        """
        from phlo_pandera import (
            AggregateConsistencyCheck,
            AggregateSpec,
            ChecksumReconciliationCheck,
            KeyParityCheck,
            MultiAggregateConsistencyCheck,
            ReconciliationCheck,
        )

        return {
            "reconciliation": ReconciliationCheck,
            "aggregate_consistency": AggregateConsistencyCheck,
            "aggregate_spec": AggregateSpec,
            "key_parity": KeyParityCheck,
            "multi_aggregate": MultiAggregateConsistencyCheck,
            "checksum": ChecksumReconciliationCheck,
        }
