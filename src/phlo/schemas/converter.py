from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, get_args, get_origin, get_type_hints

from pandera.pandas import DataFrameModel
from pyiceberg.schema import Schema
from pyiceberg.types import (
    BinaryType,
    BooleanType,
    DateType,
    DoubleType,
    LongType,
    NestedField,
    StringType,
    TimestamptzType,
)


class SchemaConversionError(Exception):
    """Raised when Pandera schema cannot be converted to PyIceberg."""

    pass


def pandera_to_iceberg(
    pandera_schema: type[DataFrameModel],
    start_field_id: int = 1,
    add_dlt_metadata: bool = True,
) -> Schema:
    """
    Convert Pandera DataFrameModel to PyIceberg Schema.

    Automatically generates PyIceberg schema from Pandera validation schema,
    eliminating the need to maintain duplicate schema definitions.

    Type Mapping:
        - str → StringType()
        - int → LongType()
        - float → DoubleType()
        - bool → BooleanType()
        - datetime → TimestamptzType()
        - date → DateType()
        - bytes → BinaryType()

    Field Metadata:
        - Pandera Field(description="...") → PyIceberg doc parameter
        - Pandera Field(nullable=False) → PyIceberg required=True
        - Pandera Field(nullable=True) → PyIceberg required=False

    Field ID Assignment:
        - Data fields: IDs 1-99 (assigned sequentially)
        - DLT metadata fields: IDs 100+ (_dlt_load_id, _dlt_id, etc.)

    Args:
        pandera_schema: Pandera DataFrameModel class to convert
        start_field_id: Starting field ID for PyIceberg (default: 1)
        add_dlt_metadata: Automatically add DLT metadata fields (default: True)

    Returns:
        PyIceberg Schema object ready for table creation

    Raises:
        SchemaConversionError: If a Pandera type cannot be mapped to PyIceberg

    Example:
        class RawData(DataFrameModel):
            id: str = Field(nullable=False, description="Unique ID")
            value: int = Field(ge=0, le=100)
            created_at: datetime

        schema = pandera_to_iceberg(RawData)
        # Returns PyIceberg Schema with 3 fields
    """
    fields: list[NestedField] = []
    field_id = start_field_id

    # Get type hints (resolves string annotations to actual types)
    try:
        annotations = get_type_hints(pandera_schema)
    except Exception as e:
        raise SchemaConversionError(
            f"Failed to get type hints from Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    if not annotations:
        raise SchemaConversionError(
            f"Pandera schema {pandera_schema.__name__} has no field annotations"
        )

    # Get Pandera schema instance to access column metadata
    try:
        pandera_schema_obj = pandera_schema.to_schema()
    except Exception as e:
        raise SchemaConversionError(
            f"Failed to instantiate Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    for field_name, field_type in annotations.items():
        # Skip internal Pandera fields and Config class
        if field_name.startswith("__") or field_name == "Config":
            continue

        # Extract metadata from Pandera column
        description = ""
        nullable = True  # Default to nullable (required=False in Iceberg)

        if field_name in pandera_schema_obj.columns:
            column = pandera_schema_obj.columns[field_name]
            nullable = column.nullable
            description = column.description or ""

        # Map Pandera type to PyIceberg type
        iceberg_type = _map_type(field_name, field_type)

        # DLT metadata fields get special IDs (100+)
        if field_name.startswith("_dlt_") or field_name == "_cascade_ingested_at":
            if field_name == "_dlt_load_id":
                current_field_id = 100
                description = description or "DLT load identifier"
                nullable = False
            elif field_name == "_dlt_id":
                current_field_id = 101
                description = description or "DLT record identifier"
                nullable = False
            elif field_name == "_cascade_ingested_at":
                current_field_id = 102
                description = description or "Phlo ingestion timestamp"
                nullable = False
            else:
                # Other DLT fields start at 103
                current_field_id = 103 + len([f for f in fields if f.field_id >= 103])
        else:
            # Regular data fields
            current_field_id = field_id
            field_id += 1

        # Create NestedField
        nested_field = NestedField(
            field_id=current_field_id,
            name=field_name,
            field_type=iceberg_type,
            required=not nullable,
            doc=description,
        )

        fields.append(nested_field)

    if not fields:
        raise SchemaConversionError(f"No fields found in Pandera schema {pandera_schema.__name__}")

    # Add DLT metadata fields (if not already present from Pandera schema)
    if add_dlt_metadata:
        existing_names = {f.name for f in fields}

        if "_dlt_load_id" not in existing_names:
            fields.append(
                NestedField(
                    field_id=100,
                    name="_dlt_load_id",
                    field_type=StringType(),
                    required=True,
                    doc="DLT load identifier",
                )
            )

        if "_dlt_id" not in existing_names:
            fields.append(
                NestedField(
                    field_id=101,
                    name="_dlt_id",
                    field_type=StringType(),
                    required=True,
                    doc="DLT record identifier",
                )
            )

    return Schema(*fields)


def _map_type(field_name: str, pandera_type: Any) -> Any:
    """
    Map Pandera type annotation to PyIceberg type.

    Args:
        field_name: Name of field (for error messages)
        pandera_type: Python type annotation from Pandera schema

    Returns:
        PyIceberg type instance

    Raises:
        SchemaConversionError: If type cannot be mapped
    """
    # Handle Optional[T] types (e.g., str | None or Optional[str])
    origin = get_origin(pandera_type)
    if origin is not None:
        args = get_args(pandera_type)
        if len(args) == 2 and type(None) in args:
            # Extract the non-None type
            pandera_type = args[0] if args[1] is type(None) else args[1]

    # Get the actual type for comparison
    # Handle both type objects and string representations
    type_name = None
    if hasattr(pandera_type, "__name__"):
        type_name = pandera_type.__name__
    elif isinstance(pandera_type, type):
        type_name = pandera_type.__name__

    # Map basic types by name
    if type_name == "str" or pandera_type is str:
        return StringType()
    elif type_name == "int" or pandera_type is int:
        return LongType()
    elif type_name == "float" or pandera_type is float:
        return DoubleType()
    elif type_name == "bool" or pandera_type is bool:
        return BooleanType()
    elif type_name == "datetime" or pandera_type is datetime:
        return TimestamptzType()
    elif type_name == "date" or pandera_type is date:
        return DateType()
    elif type_name == "bytes" or pandera_type is bytes:
        return BinaryType()
    elif type_name == "Decimal" or pandera_type is Decimal:
        return DoubleType()
    else:
        raise SchemaConversionError(
            f"Cannot map Pandera type '{pandera_type}' (type_name='{type_name}') "
            f"for field '{field_name}' to PyIceberg. "
            f"Supported types: str, int, float, bool, datetime, date, bytes"
        )
