"""Iceberg provider adapter for authoritative mutation readback."""

from __future__ import annotations

from typing import Any

from phlo.run_evidence import emit_observation
from phlo.logging import get_logger
from phlo.run_evidence.redaction import payload_checksum, safe_error_summary

logger = get_logger(__name__)


def table_state(catalog: Any, table_name: str) -> dict[str, Any]:
    """Read current Iceberg state and distinguish absent from unavailable."""
    try:
        table = catalog.load_table(table_name)
        fields = [
            {
                "field_id": field.field_id,
                "name": field.name,
                "type": str(field.field_type),
                "required": field.required,
            }
            for field in table.schema().fields
        ]
        snapshot = table.current_snapshot()
        return {
            "state": "present",
            "snapshot_id": str(snapshot.snapshot_id) if snapshot else None,
            "schema_hash": payload_checksum(fields),
            "metadata": {"snapshot": "observed" if snapshot else "absent"},
        }
    except Exception as exc:
        try:
            from pyiceberg.exceptions import NoSuchTableError
        except ImportError:
            pass
        else:
            if isinstance(exc, NoSuchTableError):
                return {
                    "state": "absent",
                    "snapshot_id": None,
                    "schema_hash": None,
                    "metadata": {},
                }
        return {
            "state": "unavailable",
            "snapshot_id": None,
            "schema_hash": None,
            "metadata": {"error_type": type(exc).__name__},
        }


def unavailable_table_state(*, phase: str, error_type: str | None = None) -> dict[str, Any]:
    """Represent a readback gap without asserting that the table is absent."""
    metadata: dict[str, Any] = {"phase": phase, "readback": "unavailable"}
    if error_type:
        metadata["error_type"] = error_type
    return {
        "state": "unavailable",
        "snapshot_id": None,
        "schema_hash": None,
        "metadata": metadata,
    }


def emit_mutation(
    *,
    context: dict[str, Any] | None,
    table_name: str,
    ref: str,
    operation: str,
    status: str,
    before: dict[str, Any],
    after: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    error: BaseException | str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    if not context or not context.get("project_id") or not context.get("run_id"):
        return
    effective_status = status
    effective_error = safe_error_summary(error) if error else None
    metadata = {"before": before, "after": after, **(extra_metadata or {})}
    if status == "success" and after.get("state") == "absent":
        metadata["outcome"] = "contradictory"
        metadata["evidence_completeness"] = "incomplete"
    elif status == "success" and after.get("state") == "unavailable":
        metadata.setdefault("outcome", "success")
        metadata["evidence_completeness"] = "incomplete"
    elif status == "failed" and after.get("state") == "unavailable":
        metadata.setdefault("outcome", "unknown")
        metadata["evidence_completeness"] = "incomplete"
    try:
        emit_observation(
            project_id=context["project_id"],
            run_id=context["run_id"],
            attempt=context.get("attempt", 1),
            observation_type="iceberg",
            status=effective_status,
            producer="phlo-iceberg",
            resources=[
                {
                    "resource_kind": "iceberg_table",
                    "role": "output",
                    "table_name": table_name,
                    "resource_identity": {
                        "resource_type": "iceberg_table",
                        "resource_id": table_name,
                        "tenant": context["project_id"],
                        "attributes": {"catalog_ref": ref},
                    },
                    "ref_name": ref,
                    "schema_hash": after.get("schema_hash"),
                    "schema_hash_before": before.get("schema_hash"),
                    "schema_hash_after": after.get("schema_hash"),
                    "snapshot_before": before.get("snapshot_id"),
                    "snapshot_after": after.get("snapshot_id"),
                    "metadata": metadata,
                }
            ],
            metrics=metrics,
            error=effective_error,
            identity_parts=(
                operation,
                table_name,
                ref,
                before.get("snapshot_id"),
                after.get("snapshot_id"),
                payload_checksum(metrics or {}),
            ),
        )
    except Exception as exc:  # noqa: BLE001 - evidence must not alter provider outcome
        logger.error(
            "iceberg_mutation_evidence_persist_failed",
            operation=operation,
            table_name=table_name,
            error_type=type(exc).__name__,
        )
