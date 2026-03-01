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
            PANDERA_CONTRACT_CHECK_NAME as _PANDERA_CONTRACT_CHECK_NAME,
        )
        from phlo_pandera import (
            AggregateConsistencyCheck as _AggregateConsistencyCheck,
        )
        from phlo_pandera import (
            AggregateSpec as _AggregateSpec,
        )
        from phlo_pandera import (
            ChecksumReconciliationCheck as _ChecksumReconciliationCheck,
        )
        from phlo_pandera import (
            CountCheck as _CountCheck,
        )
        from phlo_pandera import (
            CustomSQLCheck as _CustomSQLCheck,
        )
        from phlo_pandera import (
            FreshnessCheck as _FreshnessCheck,
        )
        from phlo_pandera import (
            KeyParityCheck as _KeyParityCheck,
        )
        from phlo_pandera import (
            MultiAggregateConsistencyCheck as _MultiAggregateConsistencyCheck,
        )
        from phlo_pandera import (
            NullCheck as _NullCheck,
        )
        from phlo_pandera import (
            PatternCheck as _PatternCheck,
        )
        from phlo_pandera import (
            QualityCheck as _QualityCheck,
        )
        from phlo_pandera import (
            QualityCheckContract as _QualityCheckContract,
        )
        from phlo_pandera import (
            RangeCheck as _RangeCheck,
        )
        from phlo_pandera import (
            ReconciliationCheck as _ReconciliationCheck,
        )
        from phlo_pandera import (
            SchemaCheck as _SchemaCheck,
        )
        from phlo_pandera import (
            UniqueCheck as _UniqueCheck,
        )
        from phlo_pandera import (
            clear_quality_checks as _clear_quality_checks,
        )
        from phlo_pandera import (
            dbt_check_name as _dbt_check_name,
        )
        from phlo_pandera import (
            get_quality_checks as _get_quality_checks,
        )
        from phlo_pandera import (
            phlo_pandera as _phlo_quality,
        )

        class _DirectImportProvider:
            """Compatibility wrapper for direct import fallback."""

            @property
            def _check_classes(self):
                return {
                    "null": _NullCheck,
                    "range": _RangeCheck,
                    "freshness": _FreshnessCheck,
                    "unique": _UniqueCheck,
                    "count": _CountCheck,
                    "schema": _SchemaCheck,
                    "pattern": _PatternCheck,
                }

            def get_decorator(self):
                return _phlo_quality

            def get_check_classes(self):
                return self._check_classes

            def get_schema_extractor(self):
                return None

            def get_reconciliation_checks(self):
                return {
                    "reconciliation": _ReconciliationCheck,
                    "aggregate_consistency": _AggregateConsistencyCheck,
                    "aggregate_spec": _AggregateSpec,
                    "key_parity": _KeyParityCheck,
                    "multi_aggregate": _MultiAggregateConsistencyCheck,
                    "checksum": _ChecksumReconciliationCheck,
                }

        _direct_provider = _DirectImportProvider()

        global get_quality_checks, clear_quality_checks, QualityCheck
        global CustomSQLCheck, QualityCheckContract, dbt_check_name
        global PANDERA_CONTRACT_CHECK_NAME
        global ReconciliationCheck, AggregateConsistencyCheck, AggregateSpec
        global KeyParityCheck, MultiAggregateConsistencyCheck, ChecksumReconciliationCheck

        get_quality_checks = _get_quality_checks
        clear_quality_checks = _clear_quality_checks
        QualityCheck = _QualityCheck
        CustomSQLCheck = _CustomSQLCheck
        QualityCheckContract = _QualityCheckContract
        dbt_check_name = _dbt_check_name
        PANDERA_CONTRACT_CHECK_NAME = _PANDERA_CONTRACT_CHECK_NAME
        ReconciliationCheck = _ReconciliationCheck
        AggregateConsistencyCheck = _AggregateConsistencyCheck
        AggregateSpec = _AggregateSpec
        KeyParityCheck = _KeyParityCheck
        MultiAggregateConsistencyCheck = _MultiAggregateConsistencyCheck
        ChecksumReconciliationCheck = _ChecksumReconciliationCheck

        return _direct_provider
    except ModuleNotFoundError:
        pass

    raise ModuleNotFoundError(
        "phlo.quality requires a quality provider. Install phlo[defaults] or phlo-pandera."
    )


_provider = _load_quality_provider()

phlo_quality = _provider.get_decorator()
_check_classes = _provider.get_check_classes()
_reconciliation_classes = _provider.get_reconciliation_checks() or {}

NullCheck = _check_classes.get("null")
RangeCheck = _check_classes.get("range")
FreshnessCheck = _check_classes.get("freshness")
UniqueCheck = _check_classes.get("unique")
CountCheck = _check_classes.get("count")
SchemaCheck = _check_classes.get("schema")
PatternCheck = _check_classes.get("pattern")


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
