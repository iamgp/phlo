# schema.py - PyIceberg schema definitions for Nightscout glucose monitoring data
# Defines structured schemas for entries and treatments tables used in the Iceberg catalog
# These schemas ensure data consistency and type safety for the raw data layer

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
    TimestamptzType,
)

# --- Schema Definitions ---
# Predefined PyIceberg schemas for different data types
# GitHub User Events Schema
# Based on GitHub API: /users/{username}/events
# UNIQUE KEY: id (GitHub event ID - globally unique per event)
GITHUB_USER_EVENTS_SCHEMA = Schema(
    NestedField(1, "id", StringType(), required=False, doc="Event ID (UNIQUE KEY)"),
    NestedField(2, "type", StringType(), required=False, doc="Event type"),
    NestedField(3, "actor", StringType(), required=False, doc="Actor information (JSON)"),
    NestedField(4, "repo", StringType(), required=False, doc="Repository information (JSON)"),
    NestedField(5, "payload", StringType(), required=False, doc="Event payload (JSON)"),
    NestedField(6, "public", BooleanType(), required=False, doc="Is event public"),
    NestedField(7, "created_at", TimestamptzType(), required=False, doc="Event creation timestamp"),
    NestedField(8, "org", StringType(), required=False, doc="Organization information (JSON)"),
    NestedField(
        9,
        "_cascade_ingested_at",
        TimestamptzType(),
        required=False,
        doc="Cascade ingestion timestamp",
    ),
    # DLT metadata fields
    NestedField(
        100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"
    ),
    NestedField(
        101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"
    ),
)

# GitHub Repository Statistics Schema
# Based on GitHub API: /repos/{owner}/{repo}/stats/*
# UNIQUE KEY: Composite of (repo_id, collection_date) - one stats snapshot per repo per day
GITHUB_REPO_STATS_SCHEMA = Schema(
    NestedField(1, "repo_name", StringType(), required=False, doc="Repository name"),
    NestedField(2, "repo_full_name", StringType(), required=False, doc="Full repository name"),
    NestedField(3, "repo_id", LongType(), required=False, doc="Repository ID (part of composite key)"),
    NestedField(4, "collection_date", StringType(), required=False, doc="Data collection date (part of composite key)"),
    NestedField(5, "contributors_data", StringType(), required=False, doc="Contributors statistics (JSON)"),
    NestedField(6, "commit_activity_data", StringType(), required=False, doc="Commit activity statistics (JSON)"),
    NestedField(7, "code_frequency_data", StringType(), required=False, doc="Code frequency statistics (JSON)"),
    NestedField(8, "participation_data", StringType(), required=False, doc="Participation statistics (JSON)"),
    NestedField(
        9,
        "_cascade_ingested_at",
        TimestamptzType(),
        required=False,
        doc="Cascade ingestion timestamp",
    ),
    # DLT metadata fields
    NestedField(
        100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"
    ),
    NestedField(
        101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"
    ),
)

# Nightscout Entries Schema
# Based on Nightscout API: /api/v1/entries
# UNIQUE KEY: _id (Nightscout's unique identifier for each glucose entry)
NIGHTSCOUT_ENTRIES_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=False, doc="Nightscout entry ID (UNIQUE KEY)"),
    NestedField(2, "sgv", LongType(), required=False, doc="Sensor glucose value (mg/dL)"),
    NestedField(3, "date", LongType(), required=False, doc="Unix timestamp (ms)"),
    NestedField(4, "date_string", TimestamptzType(), required=False, doc="ISO timestamp"),
    NestedField(5, "trend", LongType(), required=False, doc="Trend arrow value"),
    NestedField(6, "direction", StringType(), required=False, doc="Trend direction"),
    NestedField(7, "device", StringType(), required=False, doc="Device name"),
    NestedField(8, "type", StringType(), required=False, doc="Entry type"),
    NestedField(9, "utc_offset", LongType(), required=False, doc="UTC offset (minutes)"),
    NestedField(10, "sys_time", TimestamptzType(), required=False, doc="System time"),
    NestedField(
        11,
        "_cascade_ingested_at",
        TimestamptzType(),
        required=False,
        doc="Cascade ingestion timestamp",
    ),
    # DLT metadata fields
    NestedField(
        100, "_dlt_load_id", StringType(), required=True, doc="DLT load identifier"
    ),
    NestedField(
        101, "_dlt_id", StringType(), required=True, doc="DLT record identifier"
    ),
)

# Nightscout Treatments Schema
# Based on Nightscout API: /api/v1/treatments
# UNIQUE KEY: _id (Nightscout's unique identifier for each treatment record)
NIGHTSCOUT_TREATMENTS_SCHEMA = Schema(
    NestedField(1, "_id", StringType(), required=True, doc="Nightscout treatment ID (UNIQUE KEY)"),
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


# --- Helper Functions ---
# Utility functions for working with schemas
def get_schema(table_type: str) -> Schema:
    """
    Get schema by table type name.

    Args:
        table_type: Table type ("entries", "treatments", "user_events", "repo_stats")

    Returns:
        PyIceberg Schema

    Example:
        schema = get_schema("user_events")
    """
    schemas = {
        "entries": NIGHTSCOUT_ENTRIES_SCHEMA,
        "treatments": NIGHTSCOUT_TREATMENTS_SCHEMA,
    "user_events": GITHUB_USER_EVENTS_SCHEMA,
"repo_stats": GITHUB_REPO_STATS_SCHEMA,
    }

    schema = schemas.get(table_type)
    if not schema:
        raise ValueError(
            f"Unknown table type: {table_type}. Available: {list(schemas.keys())}"
        )

    return schema


def get_unique_key(table_type: str) -> str:
    """
    Get the unique key column name for a table type.

    This column is used for idempotent ingestion (deduplication on merge).

    Args:
        table_type: Table type ("entries", "treatments", "user_events", "repo_stats")

    Returns:
        Column name to use as unique key

    Example:
        unique_key = get_unique_key("entries")  # Returns "_id"
    """
    unique_keys = {
        "entries": "_id",
        "treatments": "_id",
        "user_events": "id",
        "repo_stats": "_dlt_id",  # Using DLT's generated ID for repo_stats composite key handling
    }

    key = unique_keys.get(table_type)
    if not key:
        raise ValueError(
            f"Unknown table type: {table_type}. Available: {list(unique_keys.keys())}"
        )

    return key
