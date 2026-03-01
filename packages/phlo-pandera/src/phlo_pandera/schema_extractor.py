"""Pandera SchemaExtractor implementation.

Converts a Pandera DataFrameModel subclass into a provider-agnostic
NormalizedSchema for use by storage providers and schema migration tooling.
"""

from __future__ import annotations

import types
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Union, get_args, get_origin, get_type_hints

from pandera.pandas import DataFrameModel

from phlo.capabilities.specs import FieldSpec, NormalizedSchema

_DTYPE_MAP: dict[type, str] = {
    str: "string",
    int: "int64",
    float: "float64",
    bool: "bool",
    datetime: "timestamptz",
    date: "date",
    bytes: "binary",
    Decimal: "float64",
}


def _map_dtype(python_type: type) -> str:
    """Map a scalar Python type to a canonical dtype string.

    Args:
        python_type: Scalar Python type annotation.

    Returns:
        Canonical dtype string recognised by storage providers.

    Raises:
        ValueError: If the type has no known mapping.
    """
    dtype = _DTYPE_MAP.get(python_type)
    if dtype is None:
        raise ValueError(f"Unsupported type: {python_type}")
    return dtype


def _unwrap_optional(tp: Any) -> type:
    """Unwrap Optional[T] / Union[T, None] to the inner type T.

    Returns the type unchanged when it is not an optional wrapper.
    """
    origin = get_origin(tp)
    if origin is Union or isinstance(tp, types.UnionType):
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


class PanderaSchemaExtractor:
    """Extract a NormalizedSchema from a Pandera DataFrameModel subclass."""

    def extract(self, native_schema: type[DataFrameModel]) -> NormalizedSchema:
        """Convert a Pandera DataFrameModel class into a NormalizedSchema.

        Args:
            native_schema: Pandera DataFrameModel subclass (the class, not an instance).

        Returns:
            NormalizedSchema with one FieldSpec per annotated column.
        """
        annotations = get_type_hints(native_schema)
        schema_obj = native_schema.to_schema()
        columns = schema_obj.columns

        fields: list[FieldSpec] = []
        for name, annotation in annotations.items():
            if name.startswith("__") or name == "Config":
                continue

            inner_type = _unwrap_optional(annotation)
            dtype = _map_dtype(inner_type)

            nullable = True
            if name in columns:
                nullable = columns[name].nullable

            fields.append(FieldSpec(name=name, dtype=dtype, nullable=nullable))

        return NormalizedSchema(fields=fields)
