"""Normalized schema construction and comparison helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from phlo.capabilities import FieldSpec, NormalizedSchema, SchemaChange, SchemaMigrationPlan
from phlo.capabilities.schema import default_classify_change, worst_classification
from phlo.exceptions import PhloConfigError


def normalized_schema(
    fields: Mapping[str, str] | list[FieldSpec],
    *,
    required: set[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> NormalizedSchema:
    """Build a NormalizedSchema from simple mappings or FieldSpec objects."""
    if isinstance(fields, Mapping):
        required = required or set()
        field_specs = [
            FieldSpec(name=str(name), dtype=str(dtype), nullable=str(name) not in required)
            for name, dtype in fields.items()
        ]
    else:
        field_specs = list(fields)
    return NormalizedSchema(fields=field_specs, metadata=metadata or {})


def schema_from_dataframe(df: Any) -> NormalizedSchema:
    """Infer a NormalizedSchema from a pandas-like DataFrame."""
    if not hasattr(df, "dtypes"):
        raise PhloConfigError(
            message="schema_from_dataframe expects a pandas-like DataFrame",
            suggestions=["Pass a pandas DataFrame or use schema_from_arrow for Arrow schemas."],
        )
    return NormalizedSchema(
        fields=[
            FieldSpec(name=str(name), dtype=str(dtype), nullable=True)
            for name, dtype in df.dtypes.items()
        ]
    )


def schema_from_arrow(schema: Any) -> NormalizedSchema:
    """Infer a NormalizedSchema from a pyarrow schema."""
    return NormalizedSchema(
        fields=[
            FieldSpec(name=field.name, dtype=str(field.type), nullable=field.nullable)
            for field in schema
        ]
    )


def schema_field_map(schema: NormalizedSchema) -> dict[str, FieldSpec]:
    """Return fields keyed by name."""
    return {field.name: field for field in schema.fields}


def compare_schemas(
    current: NormalizedSchema,
    desired: NormalizedSchema,
    *,
    table_name: str = "<unknown>",
) -> SchemaMigrationPlan:
    """Compare two normalized schemas and classify changes."""
    current_fields = schema_field_map(current)
    desired_fields = schema_field_map(desired)
    changes: list[SchemaChange] = []

    for name, field in desired_fields.items():
        old = current_fields.get(name)
        if old is None:
            classification = default_classify_change(
                "add",
                nullable=field.nullable,
                has_default=field.default is not None,
            )
            changes.append(SchemaChange(name, "add", None, field.dtype, classification))
            continue
        if old.dtype != field.dtype:
            classification = default_classify_change("type_change")
            changes.append(
                SchemaChange(name, "type_change", old.dtype, field.dtype, classification)
            )
        if old.nullable != field.nullable:
            change_type = "nullability_relaxed" if field.nullable else "nullability_tightened"
            classification = default_classify_change(change_type)
            changes.append(
                SchemaChange(
                    name, change_type, str(old.nullable), str(field.nullable), classification
                )
            )

    for name, field in current_fields.items():
        if name not in desired_fields:
            changes.append(SchemaChange(name, "drop", field.dtype, None, "warning"))

    classification = worst_classification([change.classification for change in changes])
    return SchemaMigrationPlan(
        table_name=table_name,
        changes=changes,
        classification=classification,
        requires_approval=classification == "breaking",
        recommendations=suggest_schema_migration(changes),
    )


def suggest_schema_migration(changes: list[SchemaChange]) -> list[str]:
    """Return human-readable migration recommendations."""
    recommendations: list[str] = []
    if any(change.change_type == "add" for change in changes):
        recommendations.append("Add nullable/defaulted columns before tightening constraints.")
    if any(change.change_type == "drop" for change in changes):
        recommendations.append(
            "Review dropped columns and confirm downstream consumers are migrated."
        )
    if any(change.classification == "breaking" for change in changes):
        recommendations.append("Apply breaking changes only after approval or on a staging branch.")
    return recommendations


def assert_schema_compatible(current: NormalizedSchema, desired: NormalizedSchema) -> None:
    """Raise when the desired schema contains breaking changes."""
    plan = compare_schemas(current, desired)
    if plan.requires_approval:
        raise PhloConfigError(
            message="Schema changes require approval",
            suggestions=[f"{change.field_name}: {change.change_type}" for change in plan.changes],
        )
