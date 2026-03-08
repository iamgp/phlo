"""Delta Lake implementation of the SchemaMigrator protocol."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, cast

import pyarrow as pa

from phlo.capabilities.schema import default_classify_change, worst_classification
from phlo.capabilities.specs import NormalizedSchema, SchemaChange, SchemaMigrationPlan
from phlo.hooks import SchemaMigrationEventContext, SchemaMigrationEventEmitter
from phlo.logging import get_logger
from phlo_delta.tables import _default_storage_options, _resolve_table_uri

logger = get_logger(__name__)

_ARROW_TYPE_MAP: dict[pa.DataType, str] = {
    pa.string(): "string",
    pa.int64(): "int64",
    pa.int32(): "int32",
    pa.float64(): "float64",
    pa.float32(): "float32",
    pa.bool_(): "bool",
    pa.date32(): "date",
    pa.binary(): "binary",
}

_WIDEN_PAIRS: set[tuple[str, str]] = {
    ("int32", "int64"),
    ("float32", "float64"),
    ("int32", "float64"),
    ("int64", "float64"),
    ("date", "timestamptz"),
}


def _arrow_type_to_dtype(arrow_type: pa.DataType) -> str:
    """Map a PyArrow type instance to a canonical dtype string."""
    dtype = _ARROW_TYPE_MAP.get(arrow_type)
    if dtype is not None:
        return dtype
    if isinstance(arrow_type, pa.TimestampType):
        if arrow_type.tz:
            return "timestamptz"
        return "timestamp"
    return str(arrow_type)


_DTYPE_TO_ARROW: dict[str, pa.DataType] = {
    "string": pa.string(),
    "int64": pa.int64(),
    "int32": pa.int32(),
    "float64": pa.float64(),
    "float32": pa.float32(),
    "bool": pa.bool_(),
    "timestamptz": pa.timestamp("us", tz="UTC"),
    "timestamp": pa.timestamp("us"),
    "date": pa.date32(),
    "binary": pa.binary(),
}


def _dtype_to_arrow_type(dtype: str) -> pa.DataType:
    """Map a canonical dtype string back to a PyArrow type."""
    result = _DTYPE_TO_ARROW.get(dtype)
    if result is None:
        raise ValueError(f"Unsupported dtype for Delta conversion: {dtype}")
    return result


@dataclass
class DeltaSchemaMigrator:
    """SchemaMigrator backed by Delta Lake tables."""

    def supported_changes(self) -> set[str]:
        """Return the set of change types supported natively by Delta Lake."""
        return {
            "add",
            "drop",
            "rename",
            "widen_type",
            "narrow_type",
            "nullability_relaxed",
            "nullability_tightened",
        }

    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a change with Delta-specific overrides.

        Delta supports rename (safe) and drop (warning, recoverable via
        time travel).  All other change types fall through to the default
        classifier.
        """
        if change_type == "rename":
            return "safe"
        if change_type == "drop":
            return "warning"
        return default_classify_change(change_type, **details)

    def diff_schema(self, *, table_name: str, desired: NormalizedSchema) -> SchemaMigrationPlan:
        """Compare *desired* schema against current Delta table schema.

        Returns a ``SchemaMigrationPlan`` describing every detected change.
        """
        from deltalake import DeltaTable

        table_uri = _resolve_table_uri(table_name)
        opts = _default_storage_options()

        dt = DeltaTable(table_uri, storage_options=opts)
        current_schema = cast(Any, dt.schema()).to_pyarrow()

        current_fields: dict[str, tuple[str, bool]] = {}
        for field in current_schema:
            current_fields[field.name] = (_arrow_type_to_dtype(field.type), field.nullable)

        desired_fields: dict[str, tuple[str, bool]] = {}
        for f in desired.fields:
            desired_fields[f.name] = (f.dtype, f.nullable)

        changes: list[SchemaChange] = []

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
            recommendations.append("Dropped columns are recoverable via Delta Lake time travel.")

        plan = SchemaMigrationPlan(
            table_name=table_name,
            changes=changes,
            classification=overall,
            recommendations=recommendations,
            requires_approval=requires_approval,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=table_name, tags={"backend": "delta"})
        )
        emitter.emit(
            status="planned",
            classification=overall,
            change_count=len(changes),
            changes=[asdict(c) for c in changes],
        )

        return plan

    def apply_plan(self, *, plan: SchemaMigrationPlan, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan against a Delta table.

        Raises ``ValueError`` if the plan contains breaking changes and
        ``approved`` is not ``True``.
        """
        if plan.requires_approval and not approved:
            raise ValueError(
                f"Plan for {plan.table_name} contains breaking changes and requires approval."
            )

        from deltalake import DeltaTable

        table_uri = _resolve_table_uri(plan.table_name)
        opts = _default_storage_options()

        dt = DeltaTable(table_uri, storage_options=opts)
        current_schema = cast(Any, dt.schema()).to_pyarrow()

        new_fields: list[pa.Field] = list(current_schema)
        applied: list[str] = []

        applied_changes: list[SchemaChange] = []
        for change in plan.changes:
            if change.change_type == "add":
                arrow_type = _dtype_to_arrow_type(change.new_value or "string")
                new_fields.append(pa.field(change.field_name, arrow_type, nullable=True))
                applied.append(f"add:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "drop":
                new_fields = [f for f in new_fields if f.name != change.field_name]
                applied.append(f"drop:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "rename":
                old_name = change.old_value or change.field_name
                new_name = change.new_value or change.field_name
                new_fields = [
                    pa.field(new_name, f.type, nullable=f.nullable) if f.name == old_name else f
                    for f in new_fields
                ]
                applied.append(f"rename:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type in {"widen_type", "narrow_type"}:
                arrow_type = _dtype_to_arrow_type(change.new_value or "string")
                new_fields = [
                    pa.field(f.name, arrow_type, nullable=f.nullable)
                    if f.name == change.field_name
                    else f
                    for f in new_fields
                ]
                applied.append(f"{change.change_type}:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "nullability_relaxed":
                new_fields = [
                    pa.field(f.name, f.type, nullable=True) if f.name == change.field_name else f
                    for f in new_fields
                ]
                applied.append(f"nullability_relaxed:{change.field_name}")
                applied_changes.append(change)
            elif change.change_type == "nullability_tightened":
                new_fields = [
                    pa.field(f.name, f.type, nullable=False) if f.name == change.field_name else f
                    for f in new_fields
                ]
                applied.append(f"nullability_tightened:{change.field_name}")
                applied_changes.append(change)

        new_schema = pa.schema(new_fields)

        empty = pa.table(
            {field.name: pa.array([], type=field.type) for field in new_schema},
            schema=new_schema,
        )

        from deltalake import write_deltalake

        write_deltalake(
            table_uri,
            empty,
            mode="overwrite",
            schema_mode="overwrite",
            storage_options=opts,
        )

        logger.info(
            "delta_schema_migration_applied",
            table_name=plan.table_name,
            applied_count=len(applied),
            changes=applied,
        )

        emitter = SchemaMigrationEventEmitter(
            SchemaMigrationEventContext(table_name=plan.table_name, tags={"backend": "delta"})
        )
        emitter.emit(
            status="applied",
            classification=plan.classification,
            change_count=len(applied),
            changes=[asdict(c) for c in applied_changes],
        )

        return {
            "status": "applied",
            "applied_count": len(applied),
            "changes_applied": applied,
        }

    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return version-level history for *table_name*."""
        from phlo_delta.tables import list_table_versions

        return list_table_versions(table_name=table_name, limit=limit)
