# PHLO-002: Schema Mismatch

**Error Type:** Discovery and Configuration Error
**Severity:** High
**Exception Class:** `PhloSchemaError`

## Description

This error occurs when there's a mismatch between your decorator configuration and your Pandera schema definition. Most commonly, this happens when the `unique_key` specified in the decorator doesn't match any field in the `validation_schema`.

## Common Causes

1. **unique_key not in schema**
   - The field specified as `unique_key` doesn't exist in your Pandera schema
   - Typo in the field name

2. **Schema field type mismatch**
   - Field exists but has incompatible type
   - Field is nullable when it should be required

3. **Schema version mismatch**
   - Using old schema definition
   - Schema was updated but decorator config wasn't

4. **Case sensitivity issues**
   - Field names are case-sensitive
   - `observation_id` ≠ `Observation_ID`

## Solutions

### Solution 1: Verify unique_key exists in schema

Check that your `unique_key` matches a field in your schema:

```python
# schemas/weather.py
from pandera import DataFrameModel, Field

class WeatherObservations(DataFrameModel):
    observation_id: str = Field(nullable=False)  # ✅ Field exists
    station_id: str = Field(nullable=False)
    temperature: float
    timestamp: datetime

# ingestion/weather.py
@cascade_ingestion(
    unique_key="observation_id",  # ✅ Matches schema field
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

### Solution 2: Fix typos with fuzzy matching

Phlo provides helpful suggestions when it detects a typo:

```python
# Error message includes suggestions:
PhloSchemaError (PHLO-002): unique_key 'observation_idd' not found in schema

Suggested actions:
  1. Did you mean 'observation_id'?
  2. Available fields: observation_id, station_id, temperature, timestamp
```

### Solution 3: Use schema inspection

Verify available fields in your schema:

```python
from phlo.schemas.weather import WeatherObservations
import pandera as pa

schema = WeatherObservations.to_schema()
print("Available fields:", list(schema.columns.keys()))
# Output: ['observation_id', 'station_id', 'temperature', 'timestamp']
```

### Solution 4: Check field case sensitivity

Ensure exact case match:

```python
# ❌ Wrong case
unique_key="Observation_ID"

# ✅ Correct case
unique_key="observation_id"
```

## Examples

### ❌ Incorrect: Typo in unique_key

```python
@cascade_ingestion(
    unique_key="observation_idd",  # ❌ Typo: extra 'd'
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

### ✅ Correct: Exact match

```python
@cascade_ingestion(
    unique_key="observation_id",  # ✅ Matches schema field exactly
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

### ❌ Incorrect: Field not in schema

```python
class WeatherObservations(DataFrameModel):
    station_id: str
    temperature: float
    # ❌ No observation_id field

@cascade_ingestion(
    unique_key="observation_id",  # ❌ Field doesn't exist
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

### ✅ Correct: All fields defined

```python
class WeatherObservations(DataFrameModel):
    observation_id: str = Field(nullable=False)  # ✅ Unique key field defined
    station_id: str
    temperature: float

@cascade_ingestion(
    unique_key="observation_id",  # ✅ Field exists in schema
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

## Debugging Steps

1. **List schema fields**
   ```python
   from phlo.schemas.weather import WeatherObservations
   schema = WeatherObservations.to_schema()
   print(list(schema.columns.keys()))
   ```

2. **Compare unique_key with schema**
   ```python
   unique_key = "observation_id"
   schema_fields = list(WeatherObservations.to_schema().columns.keys())

   if unique_key in schema_fields:
       print("✅ unique_key found in schema")
   else:
       print(f"❌ unique_key '{unique_key}' not in schema")
       print(f"Available: {schema_fields}")
   ```

3. **Check for case sensitivity**
   ```python
   # Case-insensitive search
   unique_key = "Observation_ID"
   schema_fields = list(WeatherObservations.to_schema().columns.keys())

   matches = [f for f in schema_fields if f.lower() == unique_key.lower()]
   if matches:
       print(f"Found case-insensitive match: {matches[0]}")
   ```

4. **Validate schema syntax**
   ```python
   try:
       schema = WeatherObservations.to_schema()
       print("✅ Schema is valid")
   except Exception as e:
       print(f"❌ Schema error: {e}")
   ```

## Related Errors

- [PHLO-001: Asset Not Discovered](./PHLO-001.md) - Asset import issues
- [PHLO-005: Missing Schema](./PHLO-005.md) - Schema not provided
- [PHLO-200: Schema Conversion Error](./PHLO-200.md) - Pandera → PyIceberg conversion fails

## Prevention

1. **Use constants for field names**
   ```python
   # schemas/weather.py
   class WeatherObservations(DataFrameModel):
       observation_id: str = Field(nullable=False)

   UNIQUE_KEY = "observation_id"  # ✅ Define constant

   # ingestion/weather.py
   from phlo.schemas.weather import WeatherObservations, UNIQUE_KEY

   @cascade_ingestion(
       unique_key=UNIQUE_KEY,  # ✅ Use constant to avoid typos
       validation_schema=WeatherObservations,
   )
   ```

2. **Add schema validation tests**
   ```python
   # tests/test_schemas.py
   def test_unique_key_in_schema():
       from phlo.schemas.weather import WeatherObservations

       schema = WeatherObservations.to_schema()
       assert "observation_id" in schema.columns
   ```

3. **Use IDE autocomplete**
   - Let your IDE suggest field names from the schema
   - Reduces typos

4. **Document schema fields**
   ```python
   class WeatherObservations(DataFrameModel):
       """
       Schema for weather observations.

       Fields:
           observation_id: Unique identifier (primary key)
           station_id: Weather station identifier
           temperature: Temperature in Celsius
           timestamp: Observation timestamp
       """
       observation_id: str = Field(nullable=False)
       station_id: str = Field(nullable=False)
       temperature: float
       timestamp: datetime
   ```

## Additional Resources

- [Pandera Documentation](https://pandera.readthedocs.io/)
- [Phlo Schema Guide](../TESTING_GUIDE.md#schema-definitions)
- [Python String Case Methods](https://docs.python.org/3/library/stdtypes.html#string-methods)
