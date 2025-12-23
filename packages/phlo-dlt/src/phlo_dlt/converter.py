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
    pass


def pandera_to_iceberg(
    pandera_schema: type[DataFrameModel],
    start_field_id: int = 1,
    add_dlt_metadata: bool = True,
    add_phlo_metadata: bool = True,
) -> Schema:
    reserved_field_ids: dict[str, int] = {
        "_dlt_load_id": 100,
        "_dlt_id": 101,
        "_phlo_ingested_at": 102,
        "_phlo_row_id": 103,
        "_phlo_partition_date": 104,
        "_phlo_run_id": 105,
    }
    fields: list[NestedField] = []
    next_field_id = start_field_id
    user_field_count = 0

    try:
        annotations = get_type_hints(pandera_schema)
    except Exception as e:
        raise SchemaConversionError(
            f"Failed to get type hints from Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    if not annotations:
        raise SchemaConversionError(f"Pandera schema {pandera_schema.__name__} has no field annotations")

    try:
        pandera_schema_obj = pandera_schema.to_schema()
    except Exception as e:
        raise SchemaConversionError(
            f"Failed to instantiate Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    for field_name, field_type in annotations.items():
        if field_name.startswith("__") or field_name == "Config":
            continue
        user_field_count += 1

        description = ""
        nullable = True

        if field_name in pandera_schema_obj.columns:
            column = pandera_schema_obj.columns[field_name]
            nullable = column.nullable
            description = column.description or ""

        try:
            iceberg_type = _map_type(field_name, field_type)
        except SchemaConversionError as e:
            raise SchemaConversionError(
                f"Cannot map Pandera type for field {field_name}: {e}"
            ) from e

        field_id = reserved_field_ids.get(field_name, next_field_id)
        if field_name not in reserved_field_ids:
            next_field_id += 1

        fields.append(
            NestedField(
                field_id=field_id,
                name=field_name,
                field_type=iceberg_type,
                required=not nullable,
                doc=description,
            )
        )

    if user_field_count == 0:
        raise SchemaConversionError(f"No fields found in Pandera schema {pandera_schema.__name__}")

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

    if add_phlo_metadata:
        existing_names = {f.name for f in fields}
        if "_phlo_row_id" not in existing_names:
            fields.append(
                NestedField(
                    field_id=103,
                    name="_phlo_row_id",
                    field_type=StringType(),
                    required=True,
                    doc="Phlo row-level lineage identifier (ULID)",
                )
            )
        if "_phlo_ingested_at" not in existing_names:
            fields.append(
                NestedField(
                    field_id=102,
                    name="_phlo_ingested_at",
                    field_type=TimestamptzType(),
                    required=True,
                    doc="UTC timestamp when phlo processed this record",
                )
            )
        if "_phlo_partition_date" not in existing_names:
            fields.append(
                NestedField(
                    field_id=104,
                    name="_phlo_partition_date",
                    field_type=StringType(),
                    required=True,
                    doc="Partition date used for ingestion (YYYY-MM-DD)",
                )
            )
        if "_phlo_run_id" not in existing_names:
            fields.append(
                NestedField(
                    field_id=105,
                    name="_phlo_run_id",
                    field_type=StringType(),
                    required=True,
                    doc="Dagster run ID for traceability",
                )
            )

    return Schema(*fields)


def _map_type(field_name: str, pandera_type: Any) -> Any:
    origin = get_origin(pandera_type)
    if origin is None:
        return _map_scalar(field_name, pandera_type)

    if origin is list:
        raise SchemaConversionError(f"Lists are not supported for field {field_name}")

    if origin is dict:
        raise SchemaConversionError(f"Dicts are not supported for field {field_name}")

    if origin is Any:
        return StringType()

    # Optional[T] / Union[T, None]
    if origin is type(None):
        return StringType()

    args = get_args(pandera_type)
    for arg in args:
        if arg is type(None):
            continue
        return _map_type(field_name, arg)

    return StringType()


def _map_scalar(field_name: str, t: Any) -> Any:
    if t in (str,):
        return StringType()
    if t in (int,):
        return LongType()
    if t in (float,):
        return DoubleType()
    if t in (bool,):
        return BooleanType()
    if t in (datetime,):
        return TimestamptzType()
    if t in (date,):
        return DateType()
    if t in (bytes,):
        return BinaryType()
    if t in (Decimal,):
        return DoubleType()

    raise SchemaConversionError(f"Unsupported type for field {field_name}: {t}")
