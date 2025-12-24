# PHLO-001: Asset Not Discovered

**Error Type:** Discovery and Configuration Error
**Severity:** High
**Exception Class:** `PhloDiscoveryError`

## Description

This error occurs when Dagster cannot discover your asset definitions. Phlo uses Python decorators like `@phlo_ingestion` to define assets, and Dagster needs to be able to find and load these definitions.

## Common Causes

1. **Workflow file not in the workflows path**
   - Asset lives outside the configured `workflows/` directory
   - `PHLO_WORKFLOWS_PATH` points to the wrong location

2. **Incorrect decorator usage**
   - Missing `@phlo_ingestion` or `@phlo_quality` decorator
   - Decorator applied to a non-function object

3. **Import errors in asset module**
   - Syntax errors preventing module import
   - Missing dependencies
   - Circular import issues

4. **Dagster not loading `phlo.framework.definitions`**
   - Workspace points at the wrong module
   - Dagster is not using `phlo.framework.definitions` as the entry point

## Solutions

### Solution 1: Verify workflow placement

Ensure your workflow module is under the configured workflows path (default: `workflows/`):

```
workflows/
└── ingestion/
    └── weather/
        └── observations.py
```

If you use a custom workflows directory, set `PHLO_WORKFLOWS_PATH` or update `phlo.yaml`.

### Solution 2: Ensure Dagster loads phlo.framework.definitions

Your Dagster workspace should point at `phlo.framework.definitions`:

```yaml
# workspace.yaml
load_from:
  - python_module:
      module_name: phlo.framework.definitions
```

### Solution 3: Check for import errors

Test that your asset module can be imported:

```bash
python -c "from workflows.ingestion.weather.observations import weather_observations_asset"
```

If you see an error, fix the import issue first.

### Solution 4: Verify decorator usage

Ensure you're using the decorator correctly:

```python
import phlo
from workflows.schemas.weather import WeatherObservations

@phlo_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    # Asset implementation
    pass
```

## Examples

### ❌ Incorrect: Asset outside workflows path

```
custom_assets/observations.py  # Not under workflows/
```

### ✅ Correct: Asset under workflows path

```
workflows/ingestion/weather/observations.py
```

### ❌ Incorrect: Missing decorator

```python
def weather_observations(partition: str):
    # Missing @phlo_ingestion decorator
    return fetch_weather_data(partition)
```

### ✅ Correct: Decorator applied

```python
@phlo_ingestion(
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
   from workflows.ingestion.weather.observations import weather_observations
   print(f"Asset discovered: {weather_observations}")
   ```

4. **Check for circular imports**
   ```bash
   python -m py_compile workflows/ingestion/weather/observations.py
   ```

## Related Errors

- [PHLO-005: Missing Schema](./PHLO-005.md) - Schema not provided to decorator
- [PHLO-002: Schema Mismatch](./PHLO-002.md) - unique_key not in schema

## Prevention

1. **Use consistent workflow placement**
   - Keep assets under `workflows/`
   - Follow the domain-based organization structure

2. **Test imports in CI/CD**
   ```python
   # tests/test_asset_discovery.py
   def test_all_assets_importable():
       from phlo.framework.definitions import defs
       assert len(defs.assets) > 0
   ```

3. **Use IDE auto-imports**
   - Let your IDE suggest imports automatically
   - This prevents typos in import paths

## Additional Resources

- [Dagster Asset Discovery](https://docs.dagster.io/concepts/assets/software-defined-assets)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [Phlo Asset Creation Guide](../TESTING_GUIDE.md#creating-assets)
