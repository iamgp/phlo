# PHLO-200: Schema Conversion Error

**Error Type:** Schema Conversion Error
**Severity:** High
**Exception Class:** `SchemaConversionError`

## Description

This error occurs when a Pandera schema cannot be converted to a PyIceberg schema. Phlo automatically converts Pandera `DataFrameModel` schemas to Iceberg table schemas for table creation and validation. When the conversion encounters unsupported types or structures, this error is raised.

## Common Causes

1. **Unsupported Pandera types**
   - Custom Pandera types without Iceberg equivalents
   - Complex Python types (e.g., `dict`, `set`, `tuple`)
   - Generic types that can't be mapped

2. **Complex nested schemas**
   - Deeply nested struct types
   - Recursive schema definitions
   - Variable-structure JSON columns

3. **Custom Pandera types**
   - User-defined `DataType` subclasses
   - Extension types from third-party libraries

4. **Ambiguous type annotations**
   - `Any` type annotations
   - Union types with incompatible members
   - Missing type annotations

## Solutions

### Solution 1: Use supported types

Stick to types that have direct Iceberg mappings:

```python
import pandera as pa
from typing import Optional

# ✅ All types have Iceberg equivalents
class WeatherObservations(pa.DataFrameModel):
    observation_id: str          # -> Iceberg StringType
    temperature: float           # -> Iceberg DoubleType
    pressure: int                # -> Iceberg LongType
    is_valid: bool               # -> Iceberg BooleanType
    timestamp: str               # -> Iceberg StringType
    reading: Optional[float] = pa.Field(nullable=True)  # -> Iceberg DoubleType (optional)
```

### Solution 2: Simplify complex types

Replace complex types with simple, serializable alternatives:

```python
import pandera as pa

# ❌ Complex nested type
class EventData(pa.DataFrameModel):
    metadata: dict  # Can't convert dict to Iceberg

# ✅ Flatten or serialize complex types
class EventData(pa.DataFrameModel):
    metadata_json: str  # Store as JSON string
    metadata_source: str
    metadata_version: int
```

### Solution 3: Override type mapping

If you need a specific Iceberg type, annotate the field:

```python
import pandera as pa

class SensorReadings(pa.DataFrameModel):
    sensor_id: str
    reading: float = pa.Field(ge=0)  # Maps to DoubleType
    precision_reading: pa.Float32 = pa.Field()  # Maps to FloatType
```

## Examples

### ❌ Incorrect: Unsupported type

```python
class EventLog(pa.DataFrameModel):
    event_id: str
    payload: dict           # ❌ dict has no Iceberg equivalent
    tags: list              # ❌ untyped list is ambiguous
```

### ✅ Correct: Supported types only

```python
class EventLog(pa.DataFrameModel):
    event_id: str
    payload_json: str       # ✅ Serialize to JSON string
    tags_csv: str           # ✅ Comma-separated string
```

## Debugging Steps

1. **Inspect schema fields and types**

   ```python
   from workflows.schemas.weather import WeatherObservations

   schema = WeatherObservations.to_schema()
   for col_name, col in schema.columns.items():
       print(f"{col_name}: {col.dtype}")
   ```

2. **Test conversion manually**

   ```python
   from phlo_iceberg.schema_conversion import pandera_to_iceberg
   from workflows.schemas.weather import WeatherObservations

   try:
       iceberg_schema = pandera_to_iceberg(WeatherObservations)
       print(f"✅ Conversion OK: {iceberg_schema}")
   except SchemaConversionError as e:
       print(f"❌ Conversion failed: {e}")
   ```

3. **Check Pandera type resolution**

   ```python
   import pandera as pa

   schema = WeatherObservations.to_schema()
   for name, col in schema.columns.items():
       print(f"{name}: pandera_type={col.dtype}, python_type={col.dtype.type}")
   ```

## Type Mapping Reference

| Pandera / Python Type | Iceberg Type    |
| --------------------- | --------------- |
| `str`                 | `StringType`    |
| `int`                 | `LongType`      |
| `float`               | `DoubleType`    |
| `bool`                | `BooleanType`   |
| `pa.Float32`          | `FloatType`     |
| `pa.Float64`          | `DoubleType`    |
| `pa.Int32`            | `IntegerType`   |
| `pa.Int64`            | `LongType`      |
| `bytes`               | `BinaryType`    |
| `datetime`            | `TimestampType` |
| `date`                | `DateType`      |

## Related Errors

- [PHLO-201: Type Conversion Error](./PHLO-201.md) - Individual field type conversion failed
- [PHLO-004: Validation Failed](./PHLO-004.md) - Data validation against schema failed
- [PHLO-002: Schema Mismatch](./PHLO-002.md) - Schema configuration mismatch

## Prevention

1. **Use only supported types in schemas**

   ```python
   # Supported: str, int, float, bool, Optional[T], datetime, date, bytes
   # Avoid: dict, list, set, tuple, Any, complex Union types
   ```

2. **Test schema conversion in CI**

   ```python
   # tests/test_schema_conversion.py
   from phlo_iceberg.schema_conversion import pandera_to_iceberg
   from workflows.schemas.weather import WeatherObservations

   def test_schema_converts_to_iceberg():
       iceberg_schema = pandera_to_iceberg(WeatherObservations)
       assert len(iceberg_schema.fields) > 0
   ```

3. **Serialize complex data**
   - Store JSON blobs as `str` columns
   - Flatten nested structures into top-level columns
   - Use separate tables for one-to-many relationships

## Additional Resources

- [PyIceberg Schema Documentation](https://py.iceberg.apache.org/)
- [Pandera Data Types](https://pandera.readthedocs.io/en/stable/dtypes.html)
- [Apache Iceberg Type System](https://iceberg.apache.org/spec/#schemas-and-data-types)
