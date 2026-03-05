"""Quality public API for Phlo.

This module provides the quality primitives by discovering and loading
quality provider plugins. The primary provider is phlo-pandera.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from phlo.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from phlo.plugins.base.quality_provider import QualityProviderPlugin

get_quality_checks: Callable[[], list[Any]] | None = None
clear_quality_checks: Callable[[], None] | None = None
QualityCheck: type | None = None
NullCheck: type | None = None
RangeCheck: type | None = None
FreshnessCheck: type | None = None
UniqueCheck: type | None = None
CountCheck: type | None = None
SchemaCheck: type | None = None
CustomSQLCheck: type | None = None
PatternCheck: type | None = None
ReconciliationCheck: type | None = None
AggregateConsistencyCheck: type | None = None
AggregateSpec: type | None = None
KeyParityCheck: type | None = None
MultiAggregateConsistencyCheck: type | None = None
ChecksumReconciliationCheck: type | None = None
PANDERA_CONTRACT_CHECK_NAME: str | None = None
QualityCheckContract: type | None = None
dbt_check_name: Callable[[str, str], str] | None = None
phlo_quality: Callable | None = None


def _provider_api_module(provider: QualityProviderPlugin) -> Any | None:
    """Resolve the provider package module that may expose helper exports."""
    provider_module = provider.__class__.__module__
    provider_package = provider_module.split(".", 1)[0]
    try:
        return importlib.import_module(provider_package)
    except ModuleNotFoundError:
        return None


def _load_quality_provider() -> QualityProviderPlugin | None:
    """Load quality provider via plugin discovery, with fallback to direct import."""
    global phlo_quality
    global get_quality_checks
    global clear_quality_checks
    global QualityCheck
    global NullCheck
    global RangeCheck
    global FreshnessCheck
    global UniqueCheck
    global CountCheck
    global SchemaCheck
    global CustomSQLCheck
    global PatternCheck
    global ReconciliationCheck
    global AggregateConsistencyCheck
    global AggregateSpec
    global KeyParityCheck
    global MultiAggregateConsistencyCheck
    global ChecksumReconciliationCheck
    global PANDERA_CONTRACT_CHECK_NAME
    global QualityCheckContract
    global dbt_check_name

    try:
        from phlo.plugins.discovery import discover_plugins, get_quality_provider

        discover_plugins()
        provider = get_quality_provider("pandera")
        if provider is not None:
            provider_module = _provider_api_module(provider)
            phlo_quality = provider.get_decorator()
            check_classes = provider.get_check_classes()
            NullCheck = check_classes.get("null")
            RangeCheck = check_classes.get("range")
            FreshnessCheck = check_classes.get("freshness")
            UniqueCheck = check_classes.get("unique")
            CountCheck = check_classes.get("count")
            SchemaCheck = check_classes.get("schema")
            PatternCheck = check_classes.get("pattern")
            QualityCheck = check_classes.get("quality_check")
            CustomSQLCheck = check_classes.get("custom_sql") or (
                getattr(provider_module, "CustomSQLCheck", None) if provider_module else None
            )
            rec_classes = provider.get_reconciliation_checks() or {}
            ReconciliationCheck = rec_classes.get("reconciliation")
            AggregateConsistencyCheck = rec_classes.get("aggregate_consistency")
            AggregateSpec = rec_classes.get("aggregate_spec")
            KeyParityCheck = rec_classes.get("key_parity")
            MultiAggregateConsistencyCheck = rec_classes.get("multi_aggregate")
            ChecksumReconciliationCheck = rec_classes.get("checksum")
            get_quality_checks = (
                getattr(provider_module, "get_quality_checks", None) if provider_module else None
            )
            clear_quality_checks = (
                getattr(provider_module, "clear_quality_checks", None) if provider_module else None
            )
            PANDERA_CONTRACT_CHECK_NAME = (
                getattr(provider_module, "PANDERA_CONTRACT_CHECK_NAME", None)
                if provider_module
                else None
            )
            QualityCheckContract = (
                getattr(provider_module, "QualityCheckContract", None) if provider_module else None
            )
            dbt_check_name = (
                getattr(provider_module, "dbt_check_name", None) if provider_module else None
            )
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
            phlo_pandera as _phlo_pandera,
        )

        phlo_quality = _phlo_pandera
        get_quality_checks = _get_quality_checks
        clear_quality_checks = _clear_quality_checks
        QualityCheck = _QualityCheck
        NullCheck = _NullCheck
        RangeCheck = _RangeCheck
        FreshnessCheck = _FreshnessCheck
        UniqueCheck = _UniqueCheck
        CountCheck = _CountCheck
        SchemaCheck = _SchemaCheck
        CustomSQLCheck = _CustomSQLCheck
        PatternCheck = _PatternCheck
        ReconciliationCheck = _ReconciliationCheck
        AggregateConsistencyCheck = _AggregateConsistencyCheck
        AggregateSpec = _AggregateSpec
        KeyParityCheck = _KeyParityCheck
        MultiAggregateConsistencyCheck = _MultiAggregateConsistencyCheck
        ChecksumReconciliationCheck = _ChecksumReconciliationCheck
        PANDERA_CONTRACT_CHECK_NAME = _PANDERA_CONTRACT_CHECK_NAME
        QualityCheckContract = _QualityCheckContract
        dbt_check_name = _dbt_check_name

        return None
    except ModuleNotFoundError:
        pass

    raise ModuleNotFoundError(
        "phlo.quality requires a quality provider. Install phlo[defaults] or phlo-pandera."
    )


_load_quality_provider()


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
