"""Quality public API for Phlo."""

from __future__ import annotations

from phlo.logging import get_logger

logger = get_logger(__name__)

try:
    from phlo_quality import (  # noqa: F401
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
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via optional extras
    logger.warning("phlo_quality_not_installed", exc_info=True)
    raise ModuleNotFoundError(
        "phlo.quality requires phlo-quality. Install phlo[defaults] or phlo-quality."
    ) from exc

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
