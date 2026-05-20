# PHLO-300: DLT Pipeline Failed

**Error Type:** DLT Pipeline Error
**Severity:** High
**Exception Class:** `DLTPipelineError`

## Description

This error occurs when a DLT (Data Load Tool) pipeline execution fails. Phlo uses DLT via the `phlo.ingest.dlt(...)` decorator for data ingestion, and this error wraps DLT-specific failures including source errors, destination write failures, and schema evolution conflicts.

## Common Causes

1. **Source errors**
   - API endpoint returns errors
   - Source credentials invalid or expired
   - Source rate limiting

2. **Destination errors**
   - Cannot write to Iceberg/S3 destination
   - Destination storage full
   - Destination permissions denied

3. **Schema evolution conflicts**
   - Source schema changed incompatibly
   - New columns conflict with existing types
   - Required columns removed from source

4. **Pipeline configuration errors**
   - Invalid pipeline name
   - Incorrect dataset name
   - Missing DLT secrets

## Solutions

### Solution 1: Check the DLT pipeline trace

DLT stores pipeline traces for debugging:

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="weather_pipeline",
    destination="filesystem",
)

# Check last load info
info = pipeline.last_trace
print(info)
```

### Solution 2: Verify source connectivity

Test the data source independently:

```python
# Test source function outside of DLT
from workflows.ingestion.weather.observations import fetch_weather_data

try:
    data = list(fetch_weather_data("2024-01-15"))
    print(f"✅ Source returned {len(data)} records")
except Exception as e:
    print(f"❌ Source error: {e}")
```

### Solution 3: Reset pipeline state

If the pipeline is in a broken state, reset it:

```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="weather_pipeline",
    destination="filesystem",
)

# Drop pipeline state and start fresh
pipeline.drop()
```

### Solution 4: Check DLT secrets

Ensure DLT can access required credentials:

```python
# .phlo/.env.local
WEATHER_API_KEY=your-api-key

# Or via DLT secrets
# .dlt/secrets.toml
# [sources.weather]
# api_key = "your-api-key"
```

## Examples

### ❌ Incorrect: No error context in ingestion

```python
import phlo
@phlo.ingest.dlt(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    # ❌ DLT errors will be opaque
    return requests.get(f"https://api.weather.com/{partition}").json()
```

### ✅ Correct: Source with error handling

```python
import phlo
@phlo.ingest.dlt(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    response = requests.get(
        f"https://api.weather.com/{partition}",
        timeout=30,
    )

    if response.status_code == 429:
        raise DLTPipelineError(
            message="Weather API rate limit exceeded",
            suggestions=[
                "Reduce ingestion frequency in cron schedule",
                "Implement backoff between partition fetches",
                "Check API plan rate limits",
            ],
        )

    response.raise_for_status()
    return response.json()
```

## Debugging Steps

1. **Check DLT pipeline logs**

   ```bash
   docker logs dagster-webserver 2>&1 | grep -i "dlt\|pipeline"
   ```

2. **List DLT pipelines**

   ```python
   import dlt
   pipelines = dlt.pipeline().list_pipelines()
   for p in pipelines:
       print(f"{p.pipeline_name}: {p.state}")
   ```

3. **Check source data**

   ```python
   # Test source independently
   source_data = list(your_source_function("2024-01-15"))
   print(f"Records: {len(source_data)}")
   print(f"Sample: {source_data[0] if source_data else 'empty'}")
   ```

4. **Verify destination access**

   ```bash
   # Check MinIO/S3 access
   curl -s http://localhost:9000/minio/health/live
   ```

5. **Review Dagster run logs**

   ```bash
   # In Dagster UI: Runs > Select failed run > View logs
   phlo services logs -f dagster-webserver
   ```

## Related Errors

- [PHLO-301: DLT Source Error](./PHLO-301.md) - Source-specific DLT failures
- [PHLO-006: Ingestion Failed](./PHLO-006.md) - General ingestion failures
- [PHLO-008: Infrastructure Error](./PHLO-008.md) - Infrastructure services down
- [PHLO-400: Iceberg Catalog Error](./PHLO-400.md) - Destination catalog issues

## Prevention

1. **Test sources independently**

   ```python
   # tests/test_sources.py
   def test_weather_source_returns_data():
       data = list(fetch_weather_data("2024-01-15"))
       assert len(data) > 0
       assert "observation_id" in data[0]
   ```

2. **Use DLT retry configuration**

   ```python
   @phlo.ingest.dlt(
       unique_key="observation_id",
       validation_schema=WeatherObservations,
   )
   def weather_observations(partition: str):
       return dlt.resource(
           fetch_weather_data,
           max_table_nesting=1,
       )(partition)
   ```

3. **Monitor pipeline health**
   - Check Dagster UI for failed materializations
   - Set up alerts on repeated failures
   - Review DLT traces after failures

4. **Pin source schemas**

   ```python
   # Prevent unexpected schema evolution
   @phlo.ingest.dlt(
       unique_key="observation_id",
       validation_schema=WeatherObservations,  # Schema acts as a contract
   )
   ```

## Additional Resources

- [DLT Documentation](https://dlthub.com/docs/)
- [DLT Pipeline Traces](https://dlthub.com/docs/running-in-production/running#inspect-save-and-alert-on-load-info)
- [phlo-dlt package](../packages/phlo-dlt.md)
