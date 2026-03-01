"""Iceberg implementation of the SchemaMigrator protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pyiceberg.types import (
    BinaryType,
    BooleanType,
    DateType,
    DecimalType,
    DoubleType,
    FloatType,
    IcebergType,
    IntegerType,
    LongType,
    StringType,
    TimestampType,
    TimestamptzType,
)

from phlo.capabilities.schema import default_classify_change, worst_classification
from phlo.capabilities.specs import NormalizedSchema, SchemaChange, SchemaMigrationPlan
from phlo.logging import get_logger
from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.settings import get_settings

logger = get_logger(__name__)

_ICEBERG_TYPE_MAP: dict[type[IcebergType], str] = {
    StringType: "string",
    LongType: "int64",
    IntegerType: "int32",
    DoubleType: "float64",
    FloatType: "float32",
    BooleanType: "bool",
    TimestamptzType: "timestamptz",
    TimestampType: "timestamp",
    DateType: "date",
    BinaryType: "binary",
    DecimalType: "decimal",
}

_WIDEN_PAIRS: set[tuple[str, str]] = {
    ("int32", "int64"),
    ("float32", "float64"),
    ("int32", "float64"),
    ("int64", "float64"),
    ("date", "timestamptz"),
}


def _iceberg_type_to_dtype(iceberg_type: IcebergType) -> str:
    """Map a PyIceberg type instance to a canonical dtype string."""
    dtype = _ICEBERG_TYPE_MAP.get(type(iceberg_type))
    if dtype is not None:
        return dtype
    return str(iceberg_type)


@dataclass
class IcebergSchemaMigrator:
    """SchemaMigrator backed by a PyIceberg catalog."""

    ref: str = field(default_factory=lambda: get_settings().iceberg_nessie_ref)

    def supported_changes(self) -> set[str]:
        """Return the set of change types supported natively by Iceberg."""
        return {
            "add",
            "drop",
            "rename",
            "widen_type",
            "narrow_type",
            "reorder",
            "nullability_relaxed",
            "nullability_tightened",
        }

    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a change with Iceberg-specific overrides.

        Iceberg supports native rename (safe) and native drop (warning,
        data-loss risk but reversible via snapshots).  All other change
        types fall through to the default classifier.
        """
        if change_type == "rename":
            return "safe"
        if change_type == "drop":
            return "warning"
        return default_classify_change(change_type, **details)

    def diff_schema(self, *, table_name: str, desired: NormalizedSchema) -> SchemaMigrationPlan:
        """Compare *desired* schema against current table schema.

        Returns a ``SchemaMigrationPlan`` describing every detected change.
        """
        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(table_name)
        current_schema = table.schema()

        current_fields: dict[str, tuple[str, bool]] = {}
        for f in current_schema.fields:
            current_fields[f.name] = (_iceberg_type_to_dtype(f.field_type), f.required is False)

        desired_fields: dict[str, tuple[str, bool]] = {}
        for f in desired.fields:
            desired_fields[f.name] = (f.dtype, f.nullable)

        changes: list[SchemaChange] = []

        # Added fields
        for name, (dtype, nullable) in desired_fields.items():
            if name not in current_fields:
                cls = self.classify_change("add", nullable=nullable, has_default=False)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type="add",
                        new_value=dtype,
                        classification=cls,
                    )
                )

        # Dropped fields
        for name in current_fields:
            if name not in desired_fields:
                cls = self.classify_change("drop")
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type="drop",
                        old_value=current_fields[name][0],
                        classification=cls,
                    )
                )

        # Type and nullability changes on common fields
        for name in current_fields.keys() & desired_fields.keys():
            cur_dtype, cur_nullable = current_fields[name]
            des_dtype, des_nullable = desired_fields[name]

            if cur_dtype != des_dtype:
                if (cur_dtype, des_dtype) in _WIDEN_PAIRS:
                    change_type = "widen_type"
                else:
                    change_type = "narrow_type"
                cls = self.classify_change(change_type)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type=change_type,
                        old_value=cur_dtype,
                        new_value=des_dtype,
                        classification=cls,
                    )
                )

            if cur_nullable != des_nullable:
                if des_nullable and not cur_nullable:
                    change_type = "nullability_relaxed"
                else:
                    change_type = "nullability_tightened"
                cls = self.classify_change(change_type)
                changes.append(
                    SchemaChange(
                        field_name=name,
                        change_type=change_type,
                        old_value=str(cur_nullable),
                        new_value=str(des_nullable),
                        classification=cls,
                    )
                )

        classifications = [c.classification for c in changes]
        overall = worst_classification(classifications)
        requires_approval = overall == "breaking"

        recommendations: list[str] = []
        if requires_approval:
            recommendations.append("Breaking changes detected — requires explicit approval.")
        if any(c.change_type == "drop" for c in changes):
            recommendations.append("Dropped columns are recoverable via Iceberg snapshot rollback.")

        return SchemaMigrationPlan(
            table_name=table_name,
            changes=changes,
            classification=overall,
            recommendations=recommendations,
            requires_approval=requires_approval,
        )

    def apply_plan(self, *, plan: SchemaMigrationPlan, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan against the Iceberg catalog.

        Raises ``ValueError`` if the plan contains breaking changes and
        ``approved`` is not ``True``.
        """
        if plan.requires_approval and not approved:
            raise ValueError(
                f"Plan for {plan.table_name} contains breaking changes and requires approval."
            )

        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(plan.table_name)

        applied: list[str] = []
        with table.update_schema() as update:
            for change in plan.changes:
                if change.change_type == "add":
                    iceberg_type = _dtype_to_iceberg_type(change.new_value or "string")
                    update.add_column(
                        path=change.field_name,
                        field_type=iceberg_type,
                    )
                    applied.append(f"add:{change.field_name}")
                elif change.change_type == "drop":
                    update.delete_column(path=change.field_name)
                    applied.append(f"drop:{change.field_name}")
                elif change.change_type == "rename":
                    update.rename_column(
                        path=change.old_value or change.field_name,
                        new_name=change.new_value or change.field_name,
                    )
                    applied.append(f"rename:{change.field_name}")
                elif change.change_type in {"widen_type", "narrow_type"}:
                    iceberg_type = _dtype_to_iceberg_type(change.new_value or "string")
                    update.update_column(
                        path=change.field_name,
                        field_type=iceberg_type,
                    )
                    applied.append(f"{change.change_type}:{change.field_name}")
                elif change.change_type == "nullability_relaxed":
                    update.set_column_optional(path=change.field_name)
                    applied.append(f"nullability_relaxed:{change.field_name}")
                elif change.change_type == "nullability_tightened":
                    update.set_column_required(path=change.field_name)
                    applied.append(f"nullability_tightened:{change.field_name}")

        logger.info(
            "iceberg_schema_migration_applied",
            table_name=plan.table_name,
            applied_count=len(applied),
            changes=applied,
        )

        return {
            "status": "applied",
            "applied_count": len(applied),
            "changes_applied": applied,
        }

    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return snapshot-level history for *table_name*."""
        catalog = get_catalog(ref=self.ref)
        table = catalog.load_table(table_name)

        snapshots = sorted(table.snapshots(), key=lambda s: s.timestamp_ms, reverse=True)
        results: list[dict[str, Any]] = []
        for snap in snapshots[:limit]:
            results.append(
                {
                    "snapshot_id": snap.snapshot_id,
                    "timestamp_ms": snap.timestamp_ms,
                    "summary": dict(snap.summary.additional_properties) if snap.summary else {},
                    "parent_id": snap.parent_snapshot_id,
                }
            )
        return results


# -- internal helpers --------------------------------------------------------

_DTYPE_TO_ICEBERG: dict[str, type[IcebergType]] = {
    "string": StringType,
    "int64": LongType,
    "int32": IntegerType,
    "float64": DoubleType,
    "float32": FloatType,
    "bool": BooleanType,
    "timestamptz": TimestamptzType,
    "timestamp": TimestampType,
    "date": DateType,
    "binary": BinaryType,
}


def _dtype_to_iceberg_type(dtype: str) -> IcebergType:
    """Map a canonical dtype string back to a PyIceberg type instance."""
    cls = _DTYPE_TO_ICEBERG.get(dtype)
    if cls is None:
        raise ValueError(f"Unsupported dtype for Iceberg conversion: {dtype}")
    return cls()
