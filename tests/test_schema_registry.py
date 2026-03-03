"""Tests for the schema registry module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from phlo.capabilities.specs import FieldSpec, NormalizedSchema
from phlo.schema_registry import (
    SchemaRegistry,
    _canonical_schema_json,
    _schema_hash,
    check_compatibility,
    deserialize_schema,
)


def _schema(*fields: tuple[str, str, bool]) -> NormalizedSchema:
    """Helper to build a NormalizedSchema from (name, dtype, nullable) tuples."""
    return NormalizedSchema(
        fields=[FieldSpec(name=n, dtype=d, nullable=nl) for n, d, nl in fields],
    )


class TestCanonicalSchemaJson:
    def test_deterministic_serialization(self) -> None:
        schema_a = _schema(("b", "int64", True), ("a", "string", False))
        schema_b = _schema(("a", "string", False), ("b", "int64", True))
        assert _canonical_schema_json(schema_a) == _canonical_schema_json(schema_b)

    def test_output_is_valid_json(self) -> None:
        schema = _schema(("x", "float64", True))
        result = json.loads(_canonical_schema_json(schema))
        assert "fields" in result
        assert result["fields"][0]["name"] == "x"


class TestSchemaHash:
    def test_hash_stability(self) -> None:
        canonical = _canonical_schema_json(_schema(("id", "int64", False)))
        h1 = _schema_hash(canonical)
        h2 = _schema_hash(canonical)
        assert h1 == h2
        assert len(h1) == 16

    def test_different_schemas_different_hashes(self) -> None:
        c1 = _canonical_schema_json(_schema(("id", "int64", False)))
        c2 = _canonical_schema_json(_schema(("id", "string", False)))
        assert _schema_hash(c1) != _schema_hash(c2)


class TestCheckCompatibility:
    def test_drop_is_breaking(self) -> None:
        previous = _schema(("id", "int64", False), ("name", "string", True))
        current = _schema(("id", "int64", False))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "breaking"
        assert plan.requires_approval is True
        assert any(c.change_type == "drop" for c in plan.changes)

    def test_add_nullable_is_safe(self) -> None:
        previous = _schema(("id", "int64", False))
        current = _schema(("id", "int64", False), ("email", "string", True))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "safe"
        assert plan.requires_approval is False

    def test_add_non_nullable_is_breaking(self) -> None:
        previous = _schema(("id", "int64", False))
        current = _schema(("id", "int64", False), ("email", "string", False))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "breaking"
        assert plan.requires_approval is True

    def test_add_non_nullable_with_default_is_warning(self) -> None:
        previous = _schema(("id", "int64", False))
        current = NormalizedSchema(
            fields=[
                FieldSpec(name="id", dtype="int64", nullable=False),
                FieldSpec(
                    name="email", dtype="string", nullable=False, default="unknown@example.com"
                ),
            ]
        )
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "warning"
        add_change = next(c for c in plan.changes if c.change_type == "add")
        assert add_change.classification == "warning"

    def test_widen_type_is_safe(self) -> None:
        previous = _schema(("val", "int32", True))
        current = _schema(("val", "int64", True))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "safe"
        assert any(c.change_type == "widen_type" for c in plan.changes)

    def test_narrow_type_is_breaking(self) -> None:
        previous = _schema(("val", "int64", True))
        current = _schema(("val", "int32", True))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "breaking"
        assert any(c.change_type == "narrow_type" for c in plan.changes)

    def test_nullability_tightened_is_breaking(self) -> None:
        previous = _schema(("id", "int64", True))
        current = _schema(("id", "int64", False))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "breaking"
        assert any(c.change_type == "nullability_tightened" for c in plan.changes)

    def test_nullability_relaxed_is_safe(self) -> None:
        previous = _schema(("id", "int64", False))
        current = _schema(("id", "int64", True))
        plan = check_compatibility(previous, current, table_name="t")
        assert plan.classification == "safe"
        assert any(c.change_type == "nullability_relaxed" for c in plan.changes)

    def test_no_changes(self) -> None:
        schema = _schema(("id", "int64", False), ("name", "string", True))
        plan = check_compatibility(schema, schema, table_name="t")
        assert plan.classification == "safe"
        assert plan.changes == []
        assert plan.requires_approval is False


class TestDeserializeSchema:
    def test_roundtrip(self) -> None:
        original = _schema(("id", "int64", False), ("name", "string", True))
        canonical = _canonical_schema_json(original)
        restored = deserialize_schema(canonical)
        assert len(restored.fields) == len(original.fields)
        restored_by_name = {f.name: f for f in restored.fields}
        for field in original.fields:
            assert field.name in restored_by_name
            assert restored_by_name[field.name].dtype == field.dtype
            assert restored_by_name[field.name].nullable == field.nullable

    def test_roundtrip_preserves_default(self) -> None:
        original = NormalizedSchema(
            fields=[
                FieldSpec(
                    name="email", dtype="string", nullable=False, default="unknown@example.com"
                )
            ]
        )
        canonical = _canonical_schema_json(original)
        restored = deserialize_schema(canonical)
        assert restored.fields[0].default == "unknown@example.com"


class TestSchemaRegistryPersistence:
    def test_snapshot_schema_uses_conflict_update(self) -> None:
        registry = SchemaRegistry("postgresql://example")
        registry._ensure_schema = lambda: None

        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("persisted-id",)
        connection.cursor.return_value.__enter__.return_value = cursor
        mock_connect = MagicMock()
        mock_connect.return_value.__enter__.return_value = connection

        with patch("phlo.schema_registry.psycopg2.connect", mock_connect):
            snapshot_id = registry.snapshot_schema("raw.users", _schema(("id", "int64", False)))

        assert snapshot_id == "persisted-id"
        executed_sql = cursor.execute.call_args.args[0]
        assert "ON CONFLICT (table_name, schema_hash) DO UPDATE" in executed_sql
