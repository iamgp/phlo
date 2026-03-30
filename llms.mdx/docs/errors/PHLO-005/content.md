# PHLO-005: Missing Schema (/docs/errors/PHLO-005)



**Error Type:** Discovery and Configuration Error
&#x2A;*Severity:** High
&#x2A;*Exception Class:** `PhloConfigError`

Description [#description]

This error occurs when the `validation_schema` parameter is not provided to the `@phlo_ingestion` or `@phlo_quality` decorator. Phlo requires a Pandera schema to validate data and derive Iceberg table schemas.

Common Causes [#common-causes]

1. **Missing `validation_schema` parameter**
   * Decorator called without `validation_schema` argument
   * Parameter name misspelled

2. **Schema class not imported**
   * Schema defined in another module but not imported
   * Import statement removed or commented out

3. **Typo in schema class name**
   * Class name misspelled in decorator call
   * Using wrong schema class

4. **Schema module has import errors**
   * Schema file has syntax errors
   * Schema depends on unavailable library

Solutions [#solutions]

Solution 1: Add the validation_schema parameter [#solution-1-add-the-validation_schema-parameter]

```python
from phlo_dlt.decorator import phlo_ingestion
from workflows.schemas.weather import WeatherObservations

#  Missing validation_schema
@phlo_ingestion(
    unique_key="observation_id",
)
def weather_observations(partition: str):
    pass

#  Schema provided
@phlo_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    pass
```

Solution 2: Create the schema class [#solution-2-create-the-schema-class]

If no schema exists yet, create one in `workflows/schemas/`:

```python
# workflows/schemas/weather.py
import pandera as pa
from typing import Optional

class WeatherObservations(pa.DataFrameModel):
    observation_id: str = pa.Field(unique=True)
    station_id: str
    temperature: float = pa.Field(ge=-90, le=60)
    humidity: Optional[float] = pa.Field(nullable=True, ge=0, le=100)
    timestamp: str

    class Config:
        strict = True
```

Solution 3: Fix the import [#solution-3-fix-the-import]

Ensure the schema module is importable:

```bash
python -c "from workflows.schemas.weather import WeatherObservations; print(' Import OK')"
```

If the import fails, check:

```python
#  Wrong import path
from schemas.weather import WeatherObservations

#  Correct import path
from workflows.schemas.weather import WeatherObservations
```

Examples [#examples]

Incorrect: No schema [#incorrect-no-schema]

```python
@phlo_ingestion(
    unique_key="observation_id",
)
def weather_observations(partition: str):
    return fetch_weather_data(partition)
```

Incorrect: Typo in parameter name [#incorrect-typo-in-parameter-name]

```python
@phlo_ingestion(
    unique_key="observation_id",
    schema=WeatherObservations,  #  Wrong parameter name
)
def weather_observations(partition: str):
    return fetch_weather_data(partition)
```

Correct: Schema provided [#correct-schema-provided]

```python
@phlo_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    return fetch_weather_data(partition)
```

Debugging Steps [#debugging-steps]

1. **Check decorator parameters**

   ```bash
   grep -n "phlo_ingestion\|phlo_quality" workflows/ingestion/weather/observations.py
   ```

2. **Verify schema import**

   ```python
   from workflows.schemas.weather import WeatherObservations
   print(f"Schema fields: {list(WeatherObservations.to_schema().columns.keys())}")
   ```

3. **List available schemas**

   ```bash
   find workflows/schemas -name "*.py" -not -name "__init__.py"
   ```

4. **Check for import errors**

   ```bash
   python -c "import workflows.schemas.weather" 2>&1
   ```

Related Errors [#related-errors]

* [PHLO-001: Asset Not Discovered](./PHLO-001.md) - Asset not found by Dagster
* [PHLO-002: Schema Mismatch](./PHLO-002.md) - unique\_key not in schema
* [PHLO-004: Validation Failed](./PHLO-004.md) - Data fails schema validation

Prevention [#prevention]

1. **Use IDE auto-complete**
   * Modern editors will suggest `validation_schema=` when typing decorator parameters

2. **Add a schema for every ingestion**

   ```
   workflows/
   ├── ingestion/
   │   └── weather/
   │       └── observations.py
   └── schemas/
       └── weather.py          # Schema for weather domain
   ```

3. **Test schema availability in CI**

   ```python
   # tests/test_schemas.py
   def test_all_ingestions_have_schemas():
       from phlo_dagster.framework.definitions import defs
       for asset in defs.assets:
           assert hasattr(asset, "validation_schema"), (
               f"Asset {asset.key} missing validation_schema"
           )
   ```

4. **Use a schema template**

   ```python
   # workflows/schemas/_template.py
   import pandera as pa

   class MySchema(pa.DataFrameModel):
       id: str = pa.Field(unique=True)

       class Config:
           strict = True
   ```

Additional Resources [#additional-resources]

* [Pandera DataFrameModel](https://pandera.readthedocs.io/en/stable/dataframe_models.html)
* [Phlo Asset Creation Guide](../TESTING_GUIDE.md#creating-assets)
