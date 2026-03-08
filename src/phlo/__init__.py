"""Phlo core glue package."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import version
from typing import Any

__version__ = version("phlo")

_INGESTION_EXPORTS = {"phlo_ingestion", "get_ingestion_assets"}
_CONTRACT_EXPORTS = {"Consumer", "SLA"}
_QUALITY_EXPORTS = {
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
}
_SUBMODULE_EXPORTS = {"ingestion", "metrics", "quality"}

__all__ = [
    "__version__",
    *_SUBMODULE_EXPORTS,
    *_CONTRACT_EXPORTS,
    *_INGESTION_EXPORTS,
    *_QUALITY_EXPORTS,
]


def __getattr__(name: str) -> Any:
    """Resolve top-level exports without importing optional packages eagerly.

    Args:
        name: Attribute name requested from the phlo package.

    Returns:
        The requested attribute or module.

    Raises:
        AttributeError: If the attribute is not exported by this module.
    """
    if name in _SUBMODULE_EXPORTS:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    if name in _CONTRACT_EXPORTS:
        from phlo.contracts import SLA, Consumer

        globals().update({"Consumer": Consumer, "SLA": SLA})
        return globals()[name]
    if name in _INGESTION_EXPORTS:
        from phlo.ingestion import get_ingestion_assets, phlo_ingestion

        globals().update(
            {
                "get_ingestion_assets": get_ingestion_assets,
                "phlo_ingestion": phlo_ingestion,
            }
        )
        return globals()[name]
    if name in _QUALITY_EXPORTS:
        from phlo.quality import (
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

        globals().update(
            {
                "AggregateConsistencyCheck": AggregateConsistencyCheck,
                "AggregateSpec": AggregateSpec,
                "ChecksumReconciliationCheck": ChecksumReconciliationCheck,
                "CountCheck": CountCheck,
                "CustomSQLCheck": CustomSQLCheck,
                "FreshnessCheck": FreshnessCheck,
                "KeyParityCheck": KeyParityCheck,
                "MultiAggregateConsistencyCheck": MultiAggregateConsistencyCheck,
                "NullCheck": NullCheck,
                "PANDERA_CONTRACT_CHECK_NAME": PANDERA_CONTRACT_CHECK_NAME,
                "PatternCheck": PatternCheck,
                "QualityCheck": QualityCheck,
                "QualityCheckContract": QualityCheckContract,
                "RangeCheck": RangeCheck,
                "ReconciliationCheck": ReconciliationCheck,
                "SchemaCheck": SchemaCheck,
                "UniqueCheck": UniqueCheck,
                "clear_quality_checks": clear_quality_checks,
                "dbt_check_name": dbt_check_name,
                "get_quality_checks": get_quality_checks,
                "phlo_quality": phlo_quality,
            }
        )
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Return the list of available attributes for dir()."""
    return sorted(set(__all__))
