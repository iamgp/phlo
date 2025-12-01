# PHLO-001: Asset Not Discovered

**Error Type:** Discovery and Configuration Error
**Severity:** High
**Exception Class:** `PhloDiscoveryError`

## Description

This error occurs when Dagster cannot discover your asset definitions. Phlo uses Python decorators like `@phlo.ingestion` to define assets, and Dagster needs to be able to find and load these definitions.

## Common Causes

1. **Asset not imported in definitions.py**
   - Your asset module is not imported in the Dagster definitions file
   - Dagster cannot discover assets that aren't imported

2. **Incorrect decorator usage**
   - Missing `@phlo.ingestion` decorator
   - Decorator applied to non-function object

3. **Import errors in asset module**
   - Syntax errors preventing module import
   - Missing dependencies
   - Circular import issues

4. **Asset definition outside of tracked paths**
   - Asset defined in directory not scanned by Dagster
   - Custom asset location not registered

## Solutions

### Solution 1: Import asset in definitions.py

Ensure your asset is imported in `src/phlo/definitions.py`:

```python
# definitions.py
from phlo.defs.ingestion.weather.observations import weather_observations_asset

defs = dg.Definitions(
    assets=[weather_observations_asset],
    # ... other definitions
)
```

### Solution 2: Use build_defs() pattern

If using the domain-based organization, ensure `build_defs()` is called:

```python
# src/phlo/defs/ingestion/weather/__init__.py
from phlo.defs.ingestion.weather.observations import build_defs

# Export build_defs so it can be discovered
__all__ = ["build_defs"]
```

### Solution 3: Check for import errors

Test that your asset module can be imported:

```bash
python -c "from phlo.defs.ingestion.weather.observations import weather_observations_asset"
```

If you see an error, fix the import issue first.

### Solution 4: Verify decorator usage

Ensure you're using the decorator correctly:

```python
import phlo
from phlo.schemas.weather import WeatherObservations

@phlo.ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    # Asset implementation
    pass
```

## Examples

### ❌ Incorrect: Asset not imported

```python
# definitions.py
defs = dg.Definitions(
    assets=[],  # Empty! Asset not imported
)
```

### ✅ Correct: Asset properly imported

```python
# definitions.py
from phlo.defs.ingestion.weather.observations import weather_observations

defs = dg.Definitions(
    assets=[weather_observations],
)
```

### ❌ Incorrect: Missing decorator

```python
def weather_observations(partition: str):
    # Missing @phlo.ingestion decorator
    return fetch_weather_data(partition)
```

### ✅ Correct: Decorator applied

```python
@phlo.ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    return fetch_weather_data(partition)
```

## Debugging Steps

1. **Check Dagster UI logs**
   ```bash
   docker logs dagster-webserver
   ```

2. **List all discovered assets**
   ```bash
   dagster asset list
   ```

3. **Test asset import directly**
   ```python
   from phlo.defs.ingestion.weather.observations import weather_observations
   print(f"Asset discovered: {weather_observations}")
   ```

4. **Check for circular imports**
   ```bash
   python -m py_compile src/phlo/defs/ingestion/weather/observations.py
   ```

## Related Errors

- [PHLO-005: Missing Schema](./PHLO-005.md) - Schema not provided to decorator
- [PHLO-002: Schema Mismatch](./PHLO-002.md) - unique_key not in schema

## Prevention

1. **Use consistent import patterns**
   - Always import assets in definitions.py
   - Follow the domain-based organization structure

2. **Test imports in CI/CD**
   ```python
   # tests/test_asset_discovery.py
   def test_all_assets_importable():
       from phlo.definitions import defs
       assert len(defs.assets) > 0
   ```

3. **Use IDE auto-imports**
   - Let your IDE suggest imports automatically
   - This prevents typos in import paths

## Additional Resources

- [Dagster Asset Discovery](https://docs.dagster.io/concepts/assets/software-defined-assets)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [Phlo Asset Creation Guide](../TESTING_GUIDE.md#creating-assets)
