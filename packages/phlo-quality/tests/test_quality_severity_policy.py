from __future__ import annotations

from dagster import AssetCheckSeverity

from phlo_quality.severity import (
    severity_for_dbt_test,
    severity_for_pandera_contract,
    severity_for_quality_check,
)


def test_quality_check_warn_threshold_emits_warn_severity() -> None:
    severity = severity_for_quality_check(passed=False, failure_fraction=0.5, warn_threshold=0.5)
    assert severity == AssetCheckSeverity.WARN


def test_quality_check_below_warn_threshold_emits_error_severity() -> None:
    severity = severity_for_quality_check(passed=False, failure_fraction=0.5, warn_threshold=0.49)
    assert severity == AssetCheckSeverity.ERROR


def test_pandera_contract_failure_emits_error_severity() -> None:
    assert severity_for_pandera_contract(passed=True) is None
    assert severity_for_pandera_contract(passed=False) == AssetCheckSeverity.ERROR


def test_dbt_severity_tag_overrides() -> None:
    assert severity_for_dbt_test(test_type="not_null", tags=[]) == AssetCheckSeverity.ERROR
    assert severity_for_dbt_test(test_type="accepted_values", tags=[]) == AssetCheckSeverity.WARN
    assert severity_for_dbt_test(test_type="not_null", tags=["warn"]) == AssetCheckSeverity.WARN
    assert (
        severity_for_dbt_test(test_type="accepted_values", tags=["blocking"])
        == AssetCheckSeverity.ERROR
    )
