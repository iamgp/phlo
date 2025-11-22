# PHLO-006: Ingestion Failed

**Error Type:** Runtime and Integration Error
**Severity:** High
**Exception Class:** `PhloIngestionError`

## Description

This error occurs when data ingestion fails during asset execution. This can happen due to API failures, network issues, authentication problems, or data processing errors.

## Common Causes

1. **API failures**
   - API endpoint unreachable
   - API rate limiting
   - API authentication failed
   - API returned error response

2. **Network issues**
   - Connection timeout
   - DNS resolution failed
   - Firewall blocking requests

3. **Data processing errors**
   - Invalid data format from source
   - Data transformation failed
   - Schema validation failed

4. **Resource exhaustion**
   - Out of memory
   - Disk space full
   - Connection pool exhausted

## Solutions

### Solution 1: Check API connectivity

Verify the API is reachable and responding:

```python
import requests

try:
    response = requests.get("https://api.example.com/status", timeout=5)
    response.raise_for_status()
    print(f"✅ API reachable: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ API unreachable: {e}")
```

### Solution 2: Implement retry logic

Add retry logic for transient failures:

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()

    # Retry on 500, 502, 503, 504
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

# Use in asset
@cascade_ingestion(...)
def weather_observations(partition: str):
    session = create_session_with_retries()
    response = session.get(f"https://api.weather.com/observations/{partition}")
    return response.json()
```

### Solution 3: Validate API authentication

Ensure API credentials are valid:

```python
import os

def validate_api_credentials():
    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        raise PhloIngestionError(
            message="WEATHER_API_KEY environment variable not set",
            suggestions=[
                "Set WEATHER_API_KEY environment variable",
                "Check .env file exists and is loaded",
                "Verify environment variable name spelling",
            ]
        )

    # Test credentials
    response = requests.get(
        "https://api.weather.com/auth/test",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code == 401:
        raise PhloIngestionError(
            message="API authentication failed",
            suggestions=[
                "Verify API key is valid and not expired",
                "Check API key has correct permissions",
                "Generate new API key from provider dashboard",
            ]
        )

@cascade_ingestion(...)
def weather_observations(partition: str):
    validate_api_credentials()
    # ... fetch data
```

### Solution 4: Add error handling and logging

Wrap data fetching in try/except with detailed logging:

```python
@cascade_ingestion(...)
def weather_observations(partition: str, context):
    try:
        context.log.info(f"Fetching data for partition: {partition}")

        response = requests.get(
            f"https://api.weather.com/observations/{partition}",
            timeout=30
        )

        context.log.info(f"API response status: {response.status_code}")

        response.raise_for_status()

        data = response.json()
        context.log.info(f"Fetched {len(data)} records")

        return data

    except requests.exceptions.Timeout:
        raise PhloIngestionError(
            message=f"API request timed out for partition {partition}",
            suggestions=[
                "Increase timeout value (currently 30s)",
                "Check API endpoint performance",
                "Verify network connectivity",
            ]
        )

    except requests.exceptions.HTTPError as e:
        raise PhloIngestionError(
            message=f"API returned error: {e.response.status_code}",
            suggestions=[
                f"Check API documentation for status code {e.response.status_code}",
                "Verify request parameters are correct",
                "Check API rate limits",
            ],
            cause=e
        )

    except Exception as e:
        raise PhloIngestionError(
            message=f"Unexpected error during ingestion: {type(e).__name__}",
            suggestions=[
                "Check logs for full stack trace",
                "Verify data format matches expectations",
                "Test with smaller date range",
            ],
            cause=e
        )
```

## Examples

### ❌ Incorrect: No error handling

```python
@cascade_ingestion(...)
def weather_observations(partition: str):
    # ❌ No error handling - will fail silently
    response = requests.get(f"https://api.weather.com/obs/{partition}")
    return response.json()
```

### ✅ Correct: Comprehensive error handling

```python
@cascade_ingestion(...)
def weather_observations(partition: str, context):
    try:
        context.log.info(f"Fetching data for {partition}")

        response = requests.get(
            f"https://api.weather.com/obs/{partition}",
            timeout=30,
            headers={"Authorization": f"Bearer {os.getenv('API_KEY')}"}
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError("API returned empty response")

        context.log.info(f"✅ Fetched {len(data)} records")
        return data

    except Exception as e:
        context.log.error(f"❌ Ingestion failed: {e}")
        raise PhloIngestionError(
            message=f"Failed to fetch weather data for {partition}",
            suggestions=[
                "Check API connectivity",
                "Verify API credentials",
                "Review API rate limits",
            ],
            cause=e
        )
```

## Debugging Steps

1. **Check API status**
   ```bash
   curl -I https://api.example.com/status
   ```

2. **Test API credentials**
   ```bash
   export API_KEY="your-api-key"
   curl -H "Authorization: Bearer $API_KEY" https://api.example.com/test
   ```

3. **Review Dagster logs**
   ```bash
   docker logs dagster-webserver
   docker logs dagster-daemon
   ```

4. **Test asset locally**
   ```python
   from phlo.defs.ingestion.weather.observations import weather_observations

   # Test with specific partition
   result = weather_observations(partition="2024-01-15")
   print(f"Fetched {len(result)} records")
   ```

5. **Check network connectivity**
   ```bash
   ping api.example.com
   nslookup api.example.com
   traceroute api.example.com
   ```

6. **Monitor API rate limits**
   ```python
   response = requests.get(url, headers=headers)

   # Check rate limit headers
   remaining = response.headers.get('X-RateLimit-Remaining')
   reset_time = response.headers.get('X-RateLimit-Reset')

   print(f"Rate limit remaining: {remaining}")
   print(f"Rate limit resets at: {reset_time}")
   ```

## Common API Error Codes

| Status Code | Meaning | Solution |
|------------|---------|----------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify API credentials |
| 403 | Forbidden | Check API permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Too Many Requests | Implement rate limiting |
| 500 | Internal Server Error | Retry with backoff |
| 503 | Service Unavailable | Wait and retry |
| 504 | Gateway Timeout | Increase timeout |

## Related Errors

- [PHLO-008: Infrastructure Error](./PHLO-008.md) - Infrastructure services unavailable
- [PHLO-300: DLT Pipeline Failed](./PHLO-300.md) - DLT-specific ingestion errors
- [PHLO-004: Validation Failed](./PHLO-004.md) - Data validation errors

## Prevention

1. **Implement health checks**
   ```python
   def check_api_health():
       try:
           response = requests.get("https://api.example.com/health", timeout=5)
           return response.status_code == 200
       except:
           return False

   @cascade_ingestion(...)
   def weather_observations(partition: str):
       if not check_api_health():
           raise PhloIngestionError(
               message="API health check failed",
               suggestions=["Check API status page", "Contact API provider"]
           )
       # ... proceed with ingestion
   ```

2. **Add monitoring and alerting**
   ```python
   from dagster import MetadataValue

   @cascade_ingestion(...)
   def weather_observations(partition: str, context):
       start_time = time.time()

       try:
           data = fetch_data(partition)
           duration = time.time() - start_time

           context.log_event(
               AssetMaterialization(
                   asset_key=context.asset_key,
                   metadata={
                       "records_fetched": len(data),
                       "duration_seconds": duration,
                       "partition": partition,
                   }
               )
           )

           return data
       except Exception as e:
           # Log failure for monitoring
           context.log.error(f"Ingestion failed after {time.time() - start_time}s")
           raise
   ```

3. **Use circuit breaker pattern**
   ```python
   from pybreaker import CircuitBreaker

   breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

   @cascade_ingestion(...)
   def weather_observations(partition: str):
       @breaker
       def fetch():
           return requests.get(url).json()

       return fetch()
   ```

4. **Test with mock data**
   ```python
   # tests/test_weather_ingestion.py
   from phlo.testing import mock_dlt_source

   def test_weather_ingestion():
       mock_data = [
           {"station_id": "KSFO", "temperature": 18.5, ...}
       ]

       with mock_dlt_source(data=mock_data) as source:
           result = weather_observations(partition="2024-01-15")
           assert len(result) > 0
   ```

## Additional Resources

- [Requests Library Documentation](https://docs.python-requests.org/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [API Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
