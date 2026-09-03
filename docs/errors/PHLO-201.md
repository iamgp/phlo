# PHLO-201: Type Conversion Error

**Error Type:** Type Conversion Error
**Severity:** Medium
**Exception Class:** `PhloError`

## Description

This error occurs when an individual field type cannot be mapped between Pandera and Iceberg type systems. Unlike [PHLO-200](./PHLO-200.md), which covers whole-schema conversion failures, this error is specific to a single field whose type has no known Iceberg equivalent.

## Common Causes

1. **Unsupported Python type annotation**
   - Using `Any`, `object`, or untyped generics
   - Custom classes as type annotations

2. **Ambiguous numeric types**
   - `Decimal` without precision/scale specification
   - NumPy-specific types not recognized by the converter

3. **Complex collection types**
   - `List[dict]` or `Dict[str, Any]`
   - Nested optional collections

4. **Third-party type extensions**
   - Pandas `CategoricalDtype`
   - Custom Pandera `DataType` subclasses

## Solutions

### Solution 1: Replace with a supported type

```python
import pandera as pa

# ❌ Unsupported type
class SensorData(pa.DataFrameModel):
    reading: object  # No Iceberg mapping for 'object'

# ✅ Use explicit type
class SensorData(pa.DataFrameModel):
    reading: float
```

### Solution 2: Serialize complex fields

```python
import pandera as pa

# ❌ Complex nested type
class EventData(pa.DataFrameModel):
    labels: list  # Can't map untyped list

# ✅ Serialize to string
class EventData(pa.DataFrameModel):
    labels_json: str  # Store as JSON string
```

### Solution 3: Use Pandera typed fields

```python
import pandera as pa

# ❌ Ambiguous
class Measurements(pa.DataFrameModel):
    value: object

# ✅ Explicit Pandera type
class Measurements(pa.DataFrameModel):
    value: pa.Float64 = pa.Field(ge=0)
```

## Examples

### ❌ Incorrect: Unmappable types

```python
from decimal import Decimal

class FinancialData(pa.DataFrameModel):
    amount: Decimal      # ❌ Decimal without precision
    metadata: dict       # ❌ dict type
    tags: list           # ❌ untyped list
```

### ✅ Correct: Explicit mappable types

```python
class FinancialData(pa.DataFrameModel):
    amount: float        # ✅ Maps to DoubleType
    metadata_json: str   # ✅ Serialized dict
    tags_csv: str        # ✅ Serialized list
```

## Debugging Steps

1. **Identify the failing field**

   ```python
   # The error message includes the field name and type
   # Example: "Cannot convert type 'object' for field 'metadata'"
   ```

2. **Check field type resolution**

   ```python
   from workflows.schemas.events import EventData

   schema = EventData.to_schema()
   for name, col in schema.columns.items():
       print(f"{name}: dtype={col.dtype}, python_type={col.dtype.type}")
   ```

3. **Test individual field conversion**

   ```python
   from phlo_iceberg.schema_conversion import pandera_to_iceberg

   try:
       iceberg_schema = pandera_to_iceberg(EventData)
       print(f"✅ Mapped schema: {iceberg_schema}")
   except Exception as e:
       print(f"❌ Cannot map: {e}")
   ```

## Related Errors

- [PHLO-200: Schema Conversion Error](./PHLO-200.md) - Whole schema conversion failed
- [PHLO-004: Validation Failed](./PHLO-004.md) - Data validation failed
- [PHLO-002: Schema Mismatch](./PHLO-002.md) - Schema configuration issue

## Prevention

1. **Reference the type mapping table**
   - See [PHLO-200 Type Mapping Reference](./PHLO-200.md#type-mapping-reference) for supported types

2. **Annotate all fields explicitly**

   ```python
   class MySchema(pa.DataFrameModel):
       # Always use explicit types, never 'object' or 'Any'
       id: str
       value: float
       count: int
       active: bool
   ```

3. **Test conversion for new schemas**

   ```python
   def test_new_schema_converts():
       from phlo_iceberg.schema_conversion import pandera_to_iceberg
       iceberg_schema = pandera_to_iceberg(MyNewSchema)
       assert len(iceberg_schema.fields) == len(MyNewSchema.to_schema().columns)
   ```

## Additional Resources

- [PyIceberg Type System](https://py.iceberg.apache.org/)
- [Pandera Data Types](https://pandera.readthedocs.io/en/stable/dtypes.html)
- [PHLO-200: Schema Conversion Error](./PHLO-200.md)
