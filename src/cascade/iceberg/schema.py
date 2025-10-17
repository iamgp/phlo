"""
PyIceberg schema definitions for Nightscout data.
"""

from pyiceberg.schema import Schema
from pyiceberg.types import (
    BooleanType,
    DoubleType,
    LongType,
    NestedField,
    StringType,
    TimestampType,
)

# Nightscout Entries Schema
# Based on Nightscout API: /api/v1/entries
NIGHTSCOUT_ENTRIES_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=True, doc="Nightscout entry ID"),
    NestedField(2, "sgv", LongType(), required=False, doc="Sensor glucose value (mg/dL)"),
    NestedField(3, "date", LongType(), required=True, doc="Unix timestamp (ms)"),
    NestedField(
        4, "dateString", StringType(), required=False, doc="ISO 8601 date string"
    ),
    NestedField(5, "trend", LongType(), required=False, doc="Trend arrow value"),
    NestedField(6, "direction", StringType(), required=False, doc="Trend direction"),
    NestedField(7, "device", StringType(), required=False, doc="Device name"),
    NestedField(8, "type", StringType(), required=False, doc="Entry type"),
    NestedField(9, "utcOffset", LongType(), required=False, doc="UTC offset (minutes)"),
    NestedField(10, "sysTime", StringType(), required=False, doc="System time"),
    NestedField(11, "mills", LongType(), required=False, doc="Milliseconds timestamp"),
    # DLT metadata fields
    NestedField(
        100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"
    ),
    NestedField(
        101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"
    ),
    NestedField(
        102,
        "_cascade_ingested_at",
        TimestampType(),
        required=True,
        doc="Cascade ingestion timestamp",
    ),
)

# Nightscout Treatments Schema
# Based on Nightscout API: /api/v1/treatments
NIGHTSCOUT_TREATMENTS_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=True, doc="Nightscout treatment ID"),
    NestedField(
        2, "eventType", StringType(), required=False, doc="Treatment event type"
    ),
    NestedField(3, "created_at", StringType(), required=False, doc="Creation timestamp"),
    NestedField(4, "timestamp", StringType(), required=False, doc="Treatment timestamp"),
    NestedField(5, "enteredBy", StringType(), required=False, doc="Entered by user"),
    NestedField(6, "glucose", DoubleType(), required=False, doc="Glucose value"),
    NestedField(7, "glucoseType", StringType(), required=False, doc="Glucose type"),
    NestedField(8, "units", StringType(), required=False, doc="Units (mg/dL or mmol/L)"),
    NestedField(9, "carbs", DoubleType(), required=False, doc="Carbohydrates (g)"),
    NestedField(10, "insulin", DoubleType(), required=False, doc="Insulin (units)"),
    NestedField(11, "duration", LongType(), required=False, doc="Duration (minutes)"),
    NestedField(
        12, "absorptionTime", LongType(), required=False, doc="Absorption time (minutes)"
    ),
    NestedField(13, "notes", StringType(), required=False, doc="Treatment notes"),
    NestedField(
        14, "isAnnouncement", BooleanType(), required=False, doc="Is announcement"
    ),
    NestedField(15, "protein", DoubleType(), required=False, doc="Protein (g)"),
    NestedField(16, "fat", DoubleType(), required=False, doc="Fat (g)"),
    NestedField(17, "utcOffset", LongType(), required=False, doc="UTC offset (minutes)"),
    NestedField(18, "mills", LongType(), required=False, doc="Milliseconds timestamp"),
    # DLT metadata fields
    NestedField(
        100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"
    ),
    NestedField(
        101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"
    ),
    NestedField(
        102,
        "_cascade_ingested_at",
        TimestampType(),
        required=True,
        doc="Cascade ingestion timestamp",
    ),
)


def get_schema(table_type: str) -> Schema:
    """
    Get schema by table type name.

    Args:
        table_type: Table type ("entries" or "treatments")

    Returns:
        PyIceberg Schema

    Example:
        schema = get_schema("entries")
    """
    schemas = {
        "entries": NIGHTSCOUT_ENTRIES_SCHEMA,
        "treatments": NIGHTSCOUT_TREATMENTS_SCHEMA,
    }

    schema = schemas.get(table_type)
    if not schema:
        raise ValueError(
            f"Unknown table type: {table_type}. Available: {list(schemas.keys())}"
        )

    return schema
