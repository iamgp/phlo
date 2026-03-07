"""Pandera-to-Delta (PyArrow) schema conversion utilities."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, get_args, get_origin, get_type_hints

import pyarrow as pa
from pandera.pandas import DataFrameModel

from phlo.logging import get_logger

logger = get_logger(__name__)


class SchemaConversionError(Exception):
    """Raised when a Pandera schema cannot be converted to a Delta-compatible Arrow schema."""

    pass


def pandera_to_delta(
    pandera_schema: type[DataFrameModel],
    add_dlt_metadata: bool = True,
    add_phlo_metadata: bool = True,
) -> pa.Schema:
    """Convert a Pandera DataFrameModel schema to a PyArrow schema for Delta Lake.

    Args:
        pandera_schema: Source Pandera model class.
        add_dlt_metadata: Whether to append standard DLT metadata columns.
        add_phlo_metadata: Whether to append standard Phlo metadata columns.

    Returns:
        pa.Schema: Equivalent PyArrow schema.

    Raises:
        SchemaConversionError: If conversion fails or schema is invalid.
    """
    fields: list[pa.Field] = []
    user_field_count = 0
    logger.info(
        "delta_schema_conversion_started",
        schema_name=pandera_schema.__name__,
        add_dlt_metadata=add_dlt_metadata,
        add_phlo_metadata=add_phlo_metadata,
    )

    try:
        annotations = get_type_hints(pandera_schema)
    except Exception as e:
        logger.exception(
            "delta_schema_conversion_type_hints_failed",
            schema_name=pandera_schema.__name__,
        )
        raise SchemaConversionError(
            f"Failed to get type hints from Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    if not annotations:
        logger.error(
            "delta_schema_conversion_no_annotations",
            schema_name=pandera_schema.__name__,
        )
        raise SchemaConversionError(
            f"Pandera schema {pandera_schema.__name__} has no field annotations"
        )

    try:
        pandera_schema_obj = pandera_schema.to_schema()
    except Exception as e:
        logger.exception(
            "delta_schema_conversion_schema_build_failed",
            schema_name=pandera_schema.__name__,
        )
        raise SchemaConversionError(
            f"Failed to instantiate Pandera schema {pandera_schema.__name__}: {e}"
        ) from e

    for field_name, field_type in annotations.items():
        if field_name.startswith("__") or field_name == "Config":
            continue
        user_field_count += 1

        nullable = True
        if field_name in pandera_schema_obj.columns:
            column = pandera_schema_obj.columns[field_name]
            nullable = column.nullable

        try:
            arrow_type = _map_type(field_name, field_type)
        except SchemaConversionError as e:
            logger.warning(
                "delta_schema_conversion_field_type_unsupported",
                schema_name=pandera_schema.__name__,
                field_name=field_name,
            )
            raise SchemaConversionError(
                f"Cannot map Pandera type for field {field_name}: {e}"
            ) from e

        fields.append(pa.field(field_name, arrow_type, nullable=nullable))

    if user_field_count == 0:
        logger.error(
            "delta_schema_conversion_no_fields",
            schema_name=pandera_schema.__name__,
        )
        raise SchemaConversionError(f"No fields found in Pandera schema {pandera_schema.__name__}")

    if add_dlt_metadata:
        existing_names = {f.name for f in fields}
        if "_dlt_load_id" not in existing_names:
            fields.append(pa.field("_dlt_load_id", pa.string(), nullable=False))
        if "_dlt_id" not in existing_names:
            fields.append(pa.field("_dlt_id", pa.string(), nullable=False))

    if add_phlo_metadata:
        existing_names = {f.name for f in fields}
        if "_phlo_row_id" not in existing_names:
            fields.append(pa.field("_phlo_row_id", pa.string(), nullable=False))
        if "_phlo_ingested_at" not in existing_names:
            fields.append(
                pa.field("_phlo_ingested_at", pa.timestamp("us", tz="UTC"), nullable=False)
            )
        if "_phlo_partition_date" not in existing_names:
            fields.append(pa.field("_phlo_partition_date", pa.string(), nullable=False))
        if "_phlo_run_id" not in existing_names:
            fields.append(pa.field("_phlo_run_id", pa.string(), nullable=False))

    logger.info(
        "delta_schema_conversion_finished",
        schema_name=pandera_schema.__name__,
        total_field_count=len(fields),
        user_field_count=user_field_count,
    )
    return pa.schema(fields)


def _map_type(field_name: str, pandera_type: Any) -> pa.DataType:
    """Map a Pandera-annotated type to a PyArrow type.

    Args:
        field_name: Source field name for error reporting.
        pandera_type: Annotated Python/Pandera type.

    Returns:
        Corresponding PyArrow type.

    Raises:
        SchemaConversionError: If type cannot be represented.
    """
    origin = get_origin(pandera_type)
    if origin is None:
        return _map_scalar(field_name, pandera_type)

    if origin is list:
        raise SchemaConversionError(f"Lists are not supported for field {field_name}")

    if origin is dict:
        raise SchemaConversionError(f"Dicts are not supported for field {field_name}")

    if origin is Any:
        return pa.string()

    if origin is type(None):
        return pa.string()

    args = get_args(pandera_type)
    for arg in args:
        if arg is type(None):
            continue
        return _map_type(field_name, arg)

    return pa.string()


def _map_scalar(field_name: str, t: Any) -> pa.DataType:
    """Map a scalar Python type to a PyArrow type.

    Args:
        field_name: Source field name for error reporting.
        t: Scalar Python type.

    Returns:
        Corresponding PyArrow type.

    Raises:
        SchemaConversionError: If type is unsupported.
    """
    if t in (str,):
        return pa.string()
    if t in (int,):
        return pa.int64()
    if t in (float,):
        return pa.float64()
    if t in (bool,):
        return pa.bool_()
    if t in (datetime,):
        return pa.timestamp("us", tz="UTC")
    if t in (date,):
        return pa.date32()
    if t in (bytes,):
        return pa.binary()
    if t in (Decimal,):
        return pa.float64()

    raise SchemaConversionError(f"Unsupported type for field {field_name}: {t}")
