from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from dagster import AssetCheckResult, AssetCheckSeverity, AssetKey, MetadataValue
from dagster_dbt import DagsterDbtTranslator

from phlo_quality.contract import QualityCheckContract, dbt_check_name
from phlo_quality.severity import severity_for_dbt_test


@dataclass(frozen=True, slots=True)
class DbtTestCheck:
    asset_key: AssetKey
    check_name: str
    passed: bool
    severity: AssetCheckSeverity | None
    metadata: dict[str, MetadataValue]

    def to_asset_check_result(self) -> AssetCheckResult:
        return AssetCheckResult(
            asset_key=self.asset_key,
            check_name=self.check_name,
            passed=self.passed,
            severity=self.severity,
            metadata=self.metadata,
        )


def extract_dbt_asset_checks(
    run_results: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    translator: DagsterDbtTranslator,
    partition_key: str | None,
    max_sql_chars: int = 100_000,
) -> list[AssetCheckResult]:
    nodes = manifest.get("nodes") or {}
    checks: list[AssetCheckResult] = []

    for result in run_results.get("results", []) or []:
        unique_id = result.get("unique_id")
        if not isinstance(unique_id, str) or not unique_id.startswith("test."):
            continue

        status = (result.get("status") or "").strip().lower()
        passed = status in {"pass", "skipped", "skip"}

        depends_on = result.get("depends_on") or {}
        depends_nodes = depends_on.get("nodes") or []
        target_unique_id = _first_str(depends_nodes, prefix="model.")
        if target_unique_id is None:
            target_unique_id = _first_str(depends_nodes)
        if target_unique_id is None:
            continue

        target_props = nodes.get(target_unique_id)
        if not isinstance(target_props, Mapping):
            continue

        try:
            asset_key = translator.get_asset_key(target_props)
        except Exception:
            continue

        test_props = nodes.get(unique_id, {})
        test_type = _dbt_test_type(test_props, fallback_unique_id=unique_id)
        target_name = str(
            target_props.get("name") or target_props.get("alias") or target_unique_id.split(".")[-1]
        )
        check_name = dbt_check_name(test_type, target_name)

        tags = _dbt_tags(test_props)
        failures = _int_or_none(result.get("failures"))
        failed_count = 0 if passed else (failures if failures is not None else 1)

        severity: AssetCheckSeverity | None
        if passed:
            severity = None
        elif status == "fail":
            severity = severity_for_dbt_test(test_type=test_type, tags=tags)
        else:
            severity = AssetCheckSeverity.ERROR

        compiled_sql = _dbt_compiled_sql(test_props)
        compiled_sql = _truncate(compiled_sql, max_chars=max_sql_chars)

        contract = QualityCheckContract(
            source="dbt",
            partition_key=partition_key,
            failed_count=failed_count,
            total_count=None,
            query_or_sql=compiled_sql,
            repro_sql=_repro_sql_from_sql(compiled_sql),
            sample=_sample_for_result(result, passed=passed),
        )

        metadata: dict[str, MetadataValue] = {
            **contract.to_dagster_metadata(),
            "status": MetadataValue.text(status or "unknown"),
            "test_unique_id": MetadataValue.text(unique_id),
            "test_type": MetadataValue.text(test_type),
            "target_unique_id": MetadataValue.text(target_unique_id),
            "target_name": MetadataValue.text(target_name),
        }
        if tags:
            metadata["tags"] = MetadataValue.json(sorted(tags))
        if failures is not None:
            metadata["failed_rows"] = MetadataValue.int(failures)

        checks.append(
            DbtTestCheck(
                asset_key=asset_key,
                check_name=check_name,
                passed=passed,
                severity=severity,
                metadata=metadata,
            ).to_asset_check_result()
        )

    return checks


def _first_str(values: Iterable[object], prefix: str | None = None) -> str | None:
    for value in values:
        if not isinstance(value, str):
            continue
        if prefix is not None and not value.startswith(prefix):
            continue
        return value
    return None


def _dbt_test_type(test_props: Mapping[str, Any], *, fallback_unique_id: str) -> str:
    test_metadata = test_props.get("test_metadata")
    if isinstance(test_metadata, Mapping):
        name = test_metadata.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    resource_type = test_props.get("resource_type")
    if isinstance(resource_type, str) and resource_type.strip():
        return resource_type.strip()
    return fallback_unique_id.split(".")[-1]


def _dbt_tags(test_props: Mapping[str, Any]) -> set[str]:
    tags = test_props.get("tags")
    if not isinstance(tags, list):
        return set()
    normalized: set[str] = set()
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            normalized.add(tag.strip())
    return normalized


def _dbt_compiled_sql(test_props: Mapping[str, Any]) -> str | None:
    for key in ("compiled_code", "compiled_sql", "raw_code"):
        value = test_props.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _sample_for_result(result: Mapping[str, Any], *, passed: bool) -> list[dict[str, Any]]:
    if passed:
        return []
    sample: dict[str, Any] = {}
    message = result.get("message")
    if isinstance(message, str) and message.strip():
        sample["message"] = message
    failures = _int_or_none(result.get("failures"))
    if failures is not None:
        sample["failed_rows"] = failures
    return [sample] if sample else []


def _truncate(value: str | None, *, max_chars: int) -> str | None:
    if value is None:
        return None
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 20] + "\n-- [truncated]"


def _repro_sql_from_sql(sql: str | None) -> str | None:
    if sql is None:
        return None
    trimmed = sql.strip()
    if not trimmed:
        return None
    lower = trimmed.lower()
    if "limit" in lower:
        return trimmed
    return f"{trimmed}\nLIMIT 500"


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return None
