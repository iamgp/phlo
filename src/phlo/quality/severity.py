from __future__ import annotations

from collections.abc import Iterable

from dagster import AssetCheckSeverity

DBT_WARN_TAGS = {"warn", "anomaly"}
DBT_BLOCKING_TAGS = {"blocking"}
DBT_BLOCKING_TEST_TYPES = {"not_null", "unique", "relationships"}


def normalize_dbt_tags(tags: Iterable[str] | None) -> set[str]:
    if tags is None:
        return set()
    return {tag.strip().lower() for tag in tags if tag and tag.strip()}


def severity_for_pandera_contract(*, passed: bool) -> AssetCheckSeverity | None:
    return None if passed else AssetCheckSeverity.ERROR


def severity_for_quality_check(
    *, passed: bool, failure_fraction: float, warn_threshold: float
) -> AssetCheckSeverity | None:
    if passed:
        return None
    if failure_fraction <= 0:
        return AssetCheckSeverity.ERROR
    if warn_threshold > 0 and failure_fraction <= warn_threshold:
        return AssetCheckSeverity.WARN
    return AssetCheckSeverity.ERROR


def severity_for_dbt_test(
    *, test_type: str | None, tags: Iterable[str] | None
) -> AssetCheckSeverity:
    normalized_tags = normalize_dbt_tags(tags)
    normalized_test_type = (test_type or "").strip().lower()

    if normalized_tags & DBT_BLOCKING_TAGS:
        return AssetCheckSeverity.ERROR
    if normalized_tags & DBT_WARN_TAGS:
        return AssetCheckSeverity.WARN
    if normalized_test_type in DBT_BLOCKING_TEST_TYPES:
        return AssetCheckSeverity.ERROR
    return AssetCheckSeverity.WARN
