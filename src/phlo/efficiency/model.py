"""Efficiency scoring models for table maintenance recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BYTES_PER_MIB = 1024 * 1024
SMALL_FILES_FILE_COUNT_THRESHOLD = 500
SMALL_FILES_AVERAGE_MIB_THRESHOLD = 16
SNAPSHOT_RETENTION_THRESHOLD = 100
SLOW_RUN_SECONDS_THRESHOLD = 1800


@dataclass(frozen=True, slots=True)
class TableEfficiencyInput:
    table: str
    file_count: int
    total_bytes: int
    snapshot_count: int
    latest_run_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class EfficiencyFinding:
    table: str
    code: str
    severity: str
    message: str
    recommended_action: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_read_model(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "metrics": _copy_json_like(self.metrics),
        }


def score_table_efficiency(table: TableEfficiencyInput) -> list[EfficiencyFinding]:
    findings: list[EfficiencyFinding] = []
    average_file_mib = _average_file_mib(table)

    if (
        table.file_count >= SMALL_FILES_FILE_COUNT_THRESHOLD
        and average_file_mib < SMALL_FILES_AVERAGE_MIB_THRESHOLD
    ):
        findings.append(
            EfficiencyFinding(
                table=table.table,
                code="small_files",
                severity="warning",
                message=(
                    f"{table.table} average file size is {average_file_mib:.1f} MiB "
                    f"across {table.file_count} files"
                ),
                recommended_action="compact_files",
                metrics={
                    "average_file_mib": round(average_file_mib, 1),
                    "file_count": table.file_count,
                },
            )
        )

    if table.snapshot_count >= SNAPSHOT_RETENTION_THRESHOLD:
        findings.append(
            EfficiencyFinding(
                table=table.table,
                code="snapshot_retention",
                severity="warning",
                message=(f"{table.table} has {table.snapshot_count} snapshots retained"),
                recommended_action="expire_snapshots",
                metrics={"snapshot_count": table.snapshot_count},
            )
        )

    if (
        table.latest_run_seconds is not None
        and table.latest_run_seconds >= SLOW_RUN_SECONDS_THRESHOLD
    ):
        findings.append(
            EfficiencyFinding(
                table=table.table,
                code="slow_run",
                severity="warning",
                message=(f"{table.table} latest run took {table.latest_run_seconds} seconds"),
                recommended_action="inspect_run_performance",
                metrics={"latest_run_seconds": table.latest_run_seconds},
            )
        )

    return findings


def build_efficiency_report(inputs: list[TableEfficiencyInput]) -> dict[str, Any]:
    """Build an Observatory-safe efficiency report."""
    findings = [finding for item in inputs for finding in score_table_efficiency(item)]
    return {
        "summary": {"tables_scored": len(inputs), "finding_count": len(findings)},
        "findings": [finding.to_read_model() for finding in findings],
    }


def _average_file_mib(table: TableEfficiencyInput) -> float:
    if table.file_count <= 0:
        return 0.0
    return table.total_bytes / table.file_count / BYTES_PER_MIB


def _copy_json_like(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_json_like(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json_like(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_copy_json_like(item) for item in value)
    return value
