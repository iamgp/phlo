"""Quality public API for Phlo.

This module provides the quality primitives by discovering and loading
quality provider plugins. The primary provider is phlo-pandera.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from phlo.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from phlo.plugins.base.quality_provider import QualityProviderPlugin


def _load_quality_provider() -> "QualityProviderPlugin":
    """Load quality provider via plugin discovery, with fallback to direct import."""
    try:
        from phlo.plugins.discovery import discover_plugins, get_quality_provider

        discover_plugins()
        provider = get_quality_provider("pandera")
        if provider is not None:
            return provider
    except Exception as e:
        logger.warning("quality_provider_discovery_failed", exc_info=True, error=str(e))

    try:
        from phlo_pandera import (  # noqa: F401
            PANDERA_CONTRACT_CHECK_NAME,
            AggregateConsistencyCheck,
            AggregateSpec,
            ChecksumReconciliationCheck,
            CountCheck,
            CustomSQLCheck,
            FreshnessCheck,
            KeyParityCheck,
            MultiAggregateConsistencyCheck,
            NullCheck,
            PatternCheck,
            QualityCheck,
            QualityCheckContract,
            RangeCheck,
            ReconciliationCheck,
            SchemaCheck,
            UniqueCheck,
            clear_quality_checks,
            dbt_check_name,
            get_quality_checks,
            phlo_quality,
        )

        class _DirectImportProvider:
            """Compatibility wrapper for direct import fallback."""

            @property
            def _check_classes(self):
                return {
                    "null": NullCheck,
                    "range": RangeCheck,
                    "freshness": FreshnessCheck,
                    "unique": UniqueCheck,
                    "count": CountCheck,
                    "schema": SchemaCheck,
                    "pattern": PatternCheck,
                }

            def get_decorator(self):
                return phlo_quality

            def get_check_classes(self):
                return self._check_classes

            def get_schema_extractor(self):
                return None

            def get_reconciliation_checks(self):
                return {
                    "reconciliation": ReconciliationCheck,
                    "aggregate_consistency": AggregateConsistencyCheck,
                    "aggregate_spec": AggregateSpec,
                    "key_parity": KeyParityCheck,
                    "multi_aggregate": MultiAggregateConsistencyCheck,
                    "checksum": ChecksumReconciliationCheck,
                }

        return _DirectImportProvider()
    except ModuleNotFoundError:
        pass

    raise ModuleNotFoundError(
        "phlo.quality requires a quality provider. Install phlo[defaults] or phlo-pandera."
    )


_provider = _load_quality_provider()

phlo_quality = _provider.get_decorator()
_check_classes = _provider.get_check_classes()
_reconciliation_classes = _provider.get_reconciliation_checks() or {}

get_quality_checks = None
clear_quality_checks = None
QualityCheck = _check_classes.get("quality_check")
NullCheck = _check_classes.get("null")
RangeCheck = _check_classes.get("range")
FreshnessCheck = _check_classes.get("freshness")
UniqueCheck = _check_classes.get("unique")
CountCheck = _check_classes.get("count")
SchemaCheck = _check_classes.get("schema")
CustomSQLCheck = None
PatternCheck = _check_classes.get("pattern")
ReconciliationCheck = _reconciliation_classes.get("reconciliation")
AggregateConsistencyCheck = _reconciliation_classes.get("aggregate_consistency")
AggregateSpec = _reconciliation_classes.get("aggregate_spec")
KeyParityCheck = _reconciliation_classes.get("key_parity")
MultiAggregateConsistencyCheck = _reconciliation_classes.get("multi_aggregate")
ChecksumReconciliationCheck = _reconciliation_classes.get("checksum")
PANDERA_CONTRACT_CHECK_NAME = "pandera_contract"
QualityCheckContract = None
dbt_check_name = None


__all__ = [
    "phlo_quality",
    "get_quality_checks",
    "clear_quality_checks",
    "QualityCheck",
    "NullCheck",
    "RangeCheck",
    "FreshnessCheck",
    "UniqueCheck",
    "CountCheck",
    "SchemaCheck",
    "CustomSQLCheck",
    "PatternCheck",
    "ReconciliationCheck",
    "AggregateConsistencyCheck",
    "AggregateSpec",
    "KeyParityCheck",
    "MultiAggregateConsistencyCheck",
    "ChecksumReconciliationCheck",
    "PANDERA_CONTRACT_CHECK_NAME",
    "QualityCheckContract",
    "dbt_check_name",
]
