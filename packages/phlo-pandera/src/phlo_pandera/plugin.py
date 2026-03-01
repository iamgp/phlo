"""Pandera quality provider plugin."""

from __future__ import annotations

from typing import Any, Callable

from phlo.plugins.base import PluginMetadata, QualityProviderPlugin


class PanderaQualityProvider(QualityProviderPlugin):
    """Pandera-based quality provider for Phlo."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="pandera",
            version="0.1.0",
            description="Pandera-based quality provider with schema validation and checks",
        )

    def get_decorator(self) -> Callable:
        """Return the @phlo_pandera decorator."""
        from phlo_pandera import phlo_pandera

        return phlo_pandera

    def get_check_classes(self) -> dict[str, type]:
        """Return built-in check classes."""
        from phlo_pandera import (
            CountCheck,
            FreshnessCheck,
            NullCheck,
            PatternCheck,
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
        }

    def get_schema_extractor(self) -> Any:
        """Return Pandera schema extractor."""
        from phlo_pandera import PanderaSchemaExtractor

        return PanderaSchemaExtractor

    def get_reconciliation_checks(self) -> dict[str, type] | None:
        """Return reconciliation check classes."""
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
