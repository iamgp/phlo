from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from phlo.capabilities import CheckResult
from phlo.logging import get_logger
from phlo_dbt.translator import DbtSpecTranslator

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _CheckContract:
    """Minimal check metadata contract used for dbt test outputs."""

    source: str
    failed_count: int
    partition_key: str | None = None
    total_count: int | None = None
    query_or_sql: str | None = None
    repro_sql: str | None = None
    sample: list[Any] | None = None

    def to_metadata(self) -> dict[str, Any]:
        """Export contract fields as metadata dict."""
        metadata: dict[str, Any] = {
            "source": self.source,
            "failed_count": self.failed_count,
        }
        if self.partition_key is not None:
            metadata["partition_key"] = self.partition_key
        if self.total_count is not None:
            metadata["total_count"] = self.total_count
        if self.query_or_sql is not None:
            metadata["query_or_sql"] = self.query_or_sql
        if self.repro_sql is not None:
            metadata["repro_sql"] = self.repro_sql
        if self.sample is not None:
            metadata["sample"] = self.sample[:20]
        return metadata


def _sanitize_name(value: str) -> str:
    """Normalize a string into a Dagster-safe identifier segment."""
    cleaned = "".join(char if char.isalnum() else "_" for char in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "unknown"


def _dbt_check_name(test_type: str, target: str) -> str:
    """Build canonical check name for a dbt test."""
    return f"dbt__{_sanitize_name(test_type)}__{_sanitize_name(target)}"


def _severity_for_dbt_test(*, test_type: str | None, tags: Iterable[str] | None) -> str:
    """Map dbt test metadata to severity."""
    warn_tags = {"warn", "anomaly"}
    blocking_tags = {"blocking"}
    blocking_test_types = {"not_null", "unique", "relationships"}
    normalized_tags = {tag.strip().lower() for tag in (tags or []) if tag and tag.strip()}
    normalized_test_type = (test_type or "").strip().lower()
    if normalized_tags & blocking_tags:
        return "error"
    if normalized_tags & warn_tags:
        return "warn"
    if normalized_test_type in blocking_test_types:
        return "error"
    return "warn"


def extract_dbt_asset_checks(
    run_results: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    translator: DbtSpecTranslator,
    partition_key: str | None,
    max_sql_chars: int = 100_000,
) -> list[CheckResult]:
    """Convert dbt run results into Phlo check results.

    Args:
        run_results: Parsed dbt run results payload.
        manifest: Parsed dbt manifest payload.
        translator: Translator used to resolve target asset keys.
        partition_key: Optional partition key for emitted checks.
        max_sql_chars: Maximum SQL length to include in metadata.

    Returns:
        Check results derived from dbt test nodes.
    """
    nodes = manifest.get("nodes") or {}
    checks: list[CheckResult] = []
    result_entries = run_results.get("results", []) or []
    logger.info(
        "dbt_asset_checks_extraction_started",
        result_count=len(result_entries) if isinstance(result_entries, list) else 0,
        partition_key=partition_key,
    )

    for result in result_entries:
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
            asset_key_str = translator.get_asset_key(target_props)
        except Exception:
            logger.exception(
                "dbt_asset_checks_target_translate_failed",
                test_unique_id=unique_id,
                target_unique_id=target_unique_id,
            )
            continue

        test_props = nodes.get(unique_id, {})
        test_type = _dbt_test_type(test_props, fallback_unique_id=unique_id)
        target_name = str(
            target_props.get("name") or target_props.get("alias") or target_unique_id.split(".")[-1]
        )
        check_name = _dbt_check_name(test_type, target_name)

        tags = _dbt_tags(test_props)
        failures = _int_or_none(result.get("failures"))
        failed_count = 0 if passed else (failures if failures is not None else 1)

        severity: str | None
        if passed:
            severity = None
        elif status == "fail":
            severity_label = _severity_for_dbt_test(test_type=test_type, tags=tags)
            severity = severity_label or "error"
        else:
            severity = "error"

        compiled_sql = _dbt_compiled_sql(test_props)
        compiled_sql = _truncate(compiled_sql, max_chars=max_sql_chars)

        contract = _CheckContract(
            source="dbt",
            partition_key=partition_key,
            failed_count=failed_count,
            total_count=None,
            query_or_sql=compiled_sql,
            repro_sql=_repro_sql_from_sql(compiled_sql),
            sample=_sample_for_result(result, passed=passed),
        )

        metadata: dict[str, Any] = {
            **contract.to_metadata(),
            "status": status or "unknown",
            "test_unique_id": unique_id,
            "test_type": test_type,
            "target_unique_id": target_unique_id,
            "target_name": target_name,
        }
        if tags:
            metadata["tags"] = sorted(tags)
        if failures is not None:
            metadata["failed_rows"] = failures

        checks.append(
            CheckResult(
                asset_key=asset_key_str,
                check_name=check_name,
                passed=passed,
                severity=severity,
                metadata=metadata,
            )
        )

    logger.info(
        "dbt_asset_checks_extraction_finished",
        check_count=len(checks),
        partition_key=partition_key,
    )
    return checks


def _first_str(values: Iterable[object], prefix: str | None = None) -> str | None:
    """Return the first string entry, optionally filtered by prefix.

    Args:
        values: Candidate values to inspect.
        prefix: Optional required string prefix.

    Returns:
        First matching string, or ``None``.
    """
    for value in values:
        if not isinstance(value, str):
            continue
        if prefix is not None and not value.startswith(prefix):
            continue
        return value
    return None


def _dbt_test_type(test_props: Mapping[str, Any], *, fallback_unique_id: str) -> str:
    """Infer the dbt test type label from node properties.

    Args:
        test_props: dbt test node properties.
        fallback_unique_id: Unique id used as a fallback source.

    Returns:
        Normalized dbt test type string.
    """
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
    """Extract normalized non-empty dbt tags.

    Args:
        test_props: dbt test node properties.

    Returns:
        Unique trimmed tag values.
    """
    tags = test_props.get("tags")
    if not isinstance(tags, list):
        return set()
    normalized: set[str] = set()
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            normalized.add(tag.strip())
    return normalized


def _dbt_compiled_sql(test_props: Mapping[str, Any]) -> str | None:
    """Return compiled SQL text from known dbt node keys.

    Args:
        test_props: dbt test node properties.

    Returns:
        Compiled SQL text when available, otherwise ``None``.
    """
    for key in ("compiled_code", "compiled_sql", "raw_code"):
        value = test_props.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _sample_for_result(result: Mapping[str, Any], *, passed: bool) -> list[dict[str, Any]]:
    """Build sample metadata for failed dbt tests.

    Args:
        result: dbt result entry.
        passed: Whether the test passed.

    Returns:
        Sample metadata rows for quality diagnostics.
    """
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
    """Trim long strings to a bounded size.

    Args:
        value: Candidate value to truncate.
        max_chars: Maximum output length.

    Returns:
        Original value when short enough; truncated value otherwise.
    """
    if value is None:
        return None
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 20] + "\n-- [truncated]"


def _repro_sql_from_sql(sql: str | None) -> str | None:
    """Create a reproducible SQL snippet for debugging failed checks.

    Args:
        sql: Compiled SQL string.

    Returns:
        SQL with a row limit appended when missing, or ``None``.
    """
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
    """Safely coerce a value to ``int``.

    Args:
        value: Candidate value.

    Returns:
        Parsed integer value, or ``None`` when coercion fails.
    """
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
