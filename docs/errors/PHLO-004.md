# PHLO-004: Validation Failed

**Error Type:** Validation Error
**Severity:** High
**Exception Class:** `PhloValidationError`

## Description

This error occurs when data validation fails against a Pandera schema. Phlo validates ingested data before writing to Iceberg tables, ensuring data quality constraints are met. When incoming data violates schema constraints, this error is raised with details about which fields failed validation.

## Common Causes

1. **Data doesn't match constraints**
   - Values violate `Check` constraints (e.g., `Check.greater_than(0)`)
   - String values don't match expected patterns
   - Enum values outside allowed set

2. **Type mismatches**
   - Column contains strings where integers are expected
   - Date fields in wrong format
   - Mixed types in a single column

3. **Nulls in non-nullable fields**
   - Source data contains `None`/`NaN` in required columns
   - Missing fields in source records

4. **Values out of range**
   - Numeric values outside min/max bounds
   - String lengths exceeding limits
   - Dates outside valid ranges

## Solutions

### Solution 1: Inspect the validation failure details

The error message includes which columns and checks failed:

```python
from phlo.exceptions import PhloValidationError

try:
    # Asset execution triggers validation
    pass
except PhloValidationError as e:
    print(e)  # Shows column, check, and failing values
```

### Solution 2: Fix schema constraints

Adjust your Pandera schema to match actual data:

```python
import pandera as pa

# ❌ Schema too strict
class WeatherObservations(pa.DataFrameModel):
    temperature: float = pa.Field(ge=-50, le=50)  # Rejects 51°C
    humidity: float = pa.Field(ge=0, le=100)

# ✅ Schema with realistic ranges
class WeatherObservations(pa.DataFrameModel):
    temperature: float = pa.Field(ge=-90, le=60)  # Expanded range
    humidity: float = pa.Field(ge=0, le=100)
```

### Solution 3: Handle nullable fields

Mark fields as nullable when source data may contain nulls:

```python
import pandera as pa
from typing import Optional

# ❌ All fields required
class WeatherObservations(pa.DataFrameModel):
    station_id: str
    temperature: float
    wind_speed: float  # Fails if source omits wind_speed

# ✅ Optional fields marked nullable
class WeatherObservations(pa.DataFrameModel):
    station_id: str
    temperature: float
    wind_speed: Optional[float] = pa.Field(nullable=True)
```

### Solution 4: Clean data before validation

Pre-process data to fix known issues:

```python
import phlo
@phlo.ingest.dlt(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    data = fetch_raw_data(partition)

    # Clean known issues before Phlo validates
    for record in data:
        if record.get("temperature") == "N/A":
            record["temperature"] = None
        if isinstance(record.get("wind_speed"), str):
            record["wind_speed"] = float(record["wind_speed"])

    return data
```

## Examples

### ❌ Incorrect: Schema doesn't account for source data quirks

```python
class SensorReadings(pa.DataFrameModel):
    sensor_id: str
    value: float  # Source sometimes sends "ERROR" as value
    timestamp: str
```

### ✅ Correct: Schema handles expected variations

```python
class SensorReadings(pa.DataFrameModel):
    sensor_id: str
    value: Optional[float] = pa.Field(nullable=True)
    timestamp: str = pa.Field(str_matches=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
```

## Debugging Steps

1. **Check which columns failed**

   ```bash
   docker logs dagster-webserver 2>&1 | grep "PhloValidationError"
   ```

2. **Validate data manually**

   ```python
   import pandera as pa
   from workflows.schemas.weather import WeatherObservations

   df = fetch_raw_data_as_dataframe("2024-01-15")

   try:
       WeatherObservations.validate(df)
       print("✅ Validation passed")
   except pa.errors.SchemaError as e:
       print(f"❌ Validation failed:\n{e}")
       print(f"Failure cases:\n{e.failure_cases}")
   ```

3. **Profile the data**

   ```python
   df = fetch_raw_data_as_dataframe("2024-01-15")
   print(df.dtypes)
   print(df.describe())
   print(df.isnull().sum())
   ```

4. **Test with a single record**

   ```python
   import pandas as pd
   from workflows.schemas.weather import WeatherObservations

   sample = pd.DataFrame([{"station_id": "KSFO", "temperature": 18.5}])
   WeatherObservations.validate(sample)
   ```

## Related Errors

- [PHLO-005: Missing Schema](./PHLO-005.md) - Schema not provided to decorator
- [PHLO-002: Schema Mismatch](./PHLO-002.md) - unique_key not found in schema
- [PHLO-200: Schema Conversion Error](./PHLO-200.md) - Schema cannot convert to Iceberg

## Prevention

1. **Add schema tests**

   ```python
   # tests/test_schemas.py
   import pandas as pd
   from workflows.schemas.weather import WeatherObservations

   def test_schema_validates_sample_data():
       df = pd.DataFrame([
           {"station_id": "KSFO", "temperature": 18.5, "wind_speed": 5.2},
       ])
       WeatherObservations.validate(df)
   ```

2. **Use `allow_threshold` for gradual enforcement**

   ```python
   @phlo.quality.pandera(
       validation_schema=WeatherObservations,
       allow_threshold=0.95,  # Allow up to 5% failures
   )
   ```

3. **Document expected data ranges**

   ```python
   class WeatherObservations(pa.DataFrameModel):
       """Weather station observation data.

       Temperature: -90°C to 60°C (world record extremes)
       Humidity: 0-100%
       Wind speed: 0-120 m/s (nullable for indoor stations)
       """
       temperature: float = pa.Field(ge=-90, le=60)
       humidity: float = pa.Field(ge=0, le=100)
       wind_speed: Optional[float] = pa.Field(nullable=True, ge=0, le=120)
   ```

## Additional Resources

- [Pandera Documentation](https://pandera.readthedocs.io/)
- [Pandera DataFrameModel](https://pandera.readthedocs.io/en/stable/dataframe_models.html)
- [phlo-pandera package](../packages/phlo-pandera.md)
