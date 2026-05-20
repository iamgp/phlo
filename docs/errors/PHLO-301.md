# PHLO-301: DLT Source Error

**Error Type:** DLT Source Error
**Severity:** High
**Exception Class:** `PhloError`

## Description

This error occurs when a DLT source cannot produce data. The source function — the data-fetching logic inside a `phlo.ingest.dlt(...)` asset — fails before data reaches the DLT pipeline. This is distinct from [PHLO-300](./PHLO-300.md), which covers pipeline-level failures; PHLO-301 is specific to the data source itself.

## Common Causes

1. **Source not accessible**
   - API endpoint down or unreachable
   - Database connection refused
   - File path doesn't exist

2. **Invalid credentials**
   - API key expired or revoked
   - Database password changed
   - OAuth token not refreshed

3. **Rate limiting**
   - API rate limit exceeded
   - Too many concurrent requests
   - Burst limit hit

4. **Unexpected data format**
   - API response format changed
   - CSV delimiter changed
   - JSON structure differs from expected

## Solutions

### Solution 1: Verify source accessibility

```python
import requests

# Test API endpoint directly
try:
    response = requests.get("https://api.weather.com/status", timeout=10)
    response.raise_for_status()
    print(f"✅ Source accessible: {response.status_code}")
except requests.RequestException as e:
    print(f"❌ Source not accessible: {e}")
```

### Solution 2: Check and refresh credentials

```bash
# Verify environment variables are set
echo $WEATHER_API_KEY

# Test credentials
curl -H "Authorization: Bearer $WEATHER_API_KEY" \
     https://api.weather.com/v1/test
```

```python
import os

api_key = os.getenv("WEATHER_API_KEY")
if not api_key:
    print("❌ WEATHER_API_KEY not set")
    print("Add to .phlo/.env.local: WEATHER_API_KEY=your-key")
```

### Solution 3: Handle rate limiting

```python
import phlo
import time
import requests

@phlo.ingest.dlt(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    response = requests.get(
        f"https://api.weather.com/observations/{partition}",
        headers={"Authorization": f"Bearer {os.getenv('WEATHER_API_KEY')}"},
    )

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        response = requests.get(
            f"https://api.weather.com/observations/{partition}",
            headers={"Authorization": f"Bearer {os.getenv('WEATHER_API_KEY')}"},
        )

    response.raise_for_status()
    return response.json()
```

### Solution 4: Validate response format

```python
import phlo
@phlo.ingest.dlt(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
)
def weather_observations(partition: str):
    response = requests.get(f"https://api.weather.com/observations/{partition}")
    response.raise_for_status()

    data = response.json()

    # Validate expected format
    if not isinstance(data, list):
        raise ValueError(
            f"Expected list of records, got {type(data).__name__}. "
            "API response format may have changed."
        )

    if data and "observation_id" not in data[0]:
        raise ValueError(
            f"Expected 'observation_id' field. Got keys: {list(data[0].keys())}"
        )

    return data
```

## Examples

### ❌ Incorrect: No source validation

```python
import phlo
@phlo.ingest.dlt(table_name="weather_observations", unique_key="observation_id", group="weather")
def weather_observations(partition: str):
    return requests.get(f"https://api.weather.com/{partition}").json()
```

### ✅ Correct: Source with validation and error handling

```python
import phlo
@phlo.ingest.dlt(table_name="weather_observations", unique_key="observation_id", group="weather")
def weather_observations(partition: str, context):
    context.log.info(f"Fetching from weather API for {partition}")

    response = requests.get(
        f"https://api.weather.com/observations/{partition}",
        headers={"Authorization": f"Bearer {os.getenv('WEATHER_API_KEY')}"},
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        context.log.warning(f"No data returned for partition {partition}")
        return []

    context.log.info(f"✅ Fetched {len(data)} records")
    return data
```

## Debugging Steps

1. **Test source function directly**

   ```python
   from workflows.ingestion.weather.observations import fetch_weather_data

   data = list(fetch_weather_data("2024-01-15"))
   print(f"Records: {len(data)}")
   ```

2. **Check credentials**

   ```bash
   # List relevant env vars
   env | grep -i "api_key\|secret\|token" | grep -i weather
   ```

3. **Test API with curl**

   ```bash
   curl -v -H "Authorization: Bearer $WEATHER_API_KEY" \
        "https://api.weather.com/observations/2024-01-15"
   ```

4. **Check rate limit headers**

   ```python
   response = requests.get(url, headers=headers)
   print(f"Rate-Limit-Remaining: {response.headers.get('X-RateLimit-Remaining')}")
   print(f"Rate-Limit-Reset: {response.headers.get('X-RateLimit-Reset')}")
   ```

## Related Errors

- [PHLO-300: DLT Pipeline Failed](./PHLO-300.md) - Pipeline-level DLT failures
- [PHLO-006: Ingestion Failed](./PHLO-006.md) - General ingestion failures
- [PHLO-008: Infrastructure Error](./PHLO-008.md) - Infrastructure services unavailable

## Prevention

1. **Add source health checks**

   ```python
   def check_weather_api():
       response = requests.get(
           "https://api.weather.com/health",
           timeout=5,
       )
       return response.status_code == 200
   ```

2. **Store credentials securely**
   - Use `.phlo/.env.local` for local credentials (git-ignored)
   - Use secrets management in production
   - Rotate credentials on a schedule

3. **Test sources in CI**

   ```python
   # tests/test_sources.py
   from unittest.mock import patch

   def test_weather_source_handles_errors():
       with patch("requests.get") as mock_get:
           mock_get.return_value.status_code = 500
           mock_get.return_value.raise_for_status.side_effect = (
               requests.HTTPError("500 Server Error")
           )
           with pytest.raises(requests.HTTPError):
               fetch_weather_data("2024-01-15")
   ```

4. **Implement retries with backoff**

   ```python
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry

   session = requests.Session()
   retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503])
   session.mount("https://", HTTPAdapter(max_retries=retry))
   ```

## Additional Resources

- [DLT Sources Documentation](https://dlthub.com/docs/general-usage/source)
- [Requests Library](https://docs.python-requests.org/)
- [phlo-dlt package](../packages/phlo-dlt.md)
