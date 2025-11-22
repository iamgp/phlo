# Phlo Error Documentation

Comprehensive documentation for all Phlo error codes with solutions, examples, and prevention strategies.

## Quick Reference

| Error Code | Description | Severity | Category |
|------------|-------------|----------|----------|
| [PHLO-001](#phlo-001) | Asset Not Discovered | High | Discovery |
| [PHLO-002](#phlo-002) | Schema Mismatch | High | Configuration |
| [PHLO-003](#phlo-003) | Invalid Cron Expression | Medium | Configuration |
| [PHLO-004](#phlo-004) | Validation Failed | High | Validation |
| [PHLO-005](#phlo-005) | Missing Schema | High | Configuration |
| [PHLO-006](#phlo-006) | Ingestion Failed | High | Runtime |
| [PHLO-007](#phlo-007) | Table Not Found | High | Runtime |
| [PHLO-008](#phlo-008) | Infrastructure Error | Critical | Infrastructure |
| [PHLO-200](#phlo-200) | Schema Conversion Error | High | Schema |
| [PHLO-201](#phlo-201) | Type Conversion Error | Medium | Schema |
| [PHLO-300](#phlo-300) | DLT Pipeline Failed | High | DLT |
| [PHLO-301](#phlo-301) | DLT Source Error | High | DLT |
| [PHLO-400](#phlo-400) | Iceberg Catalog Error | High | Iceberg |
| [PHLO-401](#phlo-401) | Iceberg Table Error | High | Iceberg |
| [PHLO-402](#phlo-402) | Iceberg Write Error | High | Iceberg |

## Error Categories

### Discovery and Configuration Errors (PHLO-001 to PHLO-099)

Errors related to asset discovery, configuration, and setup.

#### PHLO-001: Asset Not Discovered
**Exception:** `PhloDiscoveryError`

Dagster cannot discover your asset definitions.

**Common causes:**
- Asset not imported in definitions.py
- Missing decorator
- Import errors in asset module

**Quick fix:**
```python
# definitions.py
from phlo.defs.ingestion.weather.observations import weather_observations

defs = dg.Definitions(assets=[weather_observations])
```

[**Full Documentation →**](./PHLO-001.md)

---

#### PHLO-002: Schema Mismatch
**Exception:** `PhloSchemaError`

Mismatch between decorator configuration and Pandera schema.

**Common causes:**
- unique_key not in schema
- Typo in field name
- Case sensitivity issues

**Quick fix:**
```python
# Verify unique_key matches schema field
@cascade_ingestion(
    unique_key="observation_id",  # Must match schema field exactly
    validation_schema=WeatherObservations,
)
```

[**Full Documentation →**](./PHLO-002.md)

---

#### PHLO-003: Invalid Cron Expression
**Exception:** `PhloCronError`

Invalid or malformed cron schedule expression.

**Common causes:**
- Wrong number of fields (need 5)
- Invalid field values
- Incorrect syntax

**Quick fix:**
```python
# Use standard 5-field cron format
@cascade_ingestion(
    cron="0 */1 * * *",  # minute hour day month weekday
    ...
)
```

**Test your cron:** [crontab.guru](https://crontab.guru)

[**Full Documentation →**](./PHLO-003.md)

---

#### PHLO-004: Validation Failed
**Exception:** `PhloValidationError`

Data validation failed against Pandera schema.

**Common causes:**
- Data doesn't match schema constraints
- Type mismatches
- Null values in non-nullable fields
- Values out of allowed range

**Quick fix:**
```python
# Check Pandera validation errors in logs
# Fix data transformation to match schema constraints
```

[**Full Documentation →**](./PHLO-004.md)

---

#### PHLO-005: Missing Schema
**Exception:** `PhloConfigError`

Validation schema not provided to decorator.

**Common causes:**
- validation_schema parameter missing
- Schema class not imported
- Typo in schema name

**Quick fix:**
```python
from phlo.schemas.weather import WeatherObservations

@cascade_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,  # ✅ Required
)
```

[**Full Documentation →**](./PHLO-005.md)

---

### Runtime and Integration Errors (PHLO-006 to PHLO-099)

Errors during asset execution and external integrations.

#### PHLO-006: Ingestion Failed
**Exception:** `PhloIngestionError`

Data ingestion failed during asset execution.

**Common causes:**
- API failures
- Network issues
- Authentication problems
- Data processing errors

**Quick fix:**
```python
# Add retry logic and error handling
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
session.mount("http://", HTTPAdapter(max_retries=retry))
```

[**Full Documentation →**](./PHLO-006.md)

---

#### PHLO-007: Table Not Found
**Exception:** `PhloTableError`

Iceberg table not found in catalog.

**Common causes:**
- Table hasn't been created yet
- Wrong table name
- Wrong catalog/namespace
- Permissions issue

**Quick fix:**
```python
# Verify table exists in Iceberg catalog
from phlo.iceberg.catalog import get_catalog

catalog = get_catalog()
tables = catalog.list_tables("bronze")
print(f"Available tables: {tables}")
```

[**Full Documentation →**](./PHLO-007.md)

---

#### PHLO-008: Infrastructure Error
**Exception:** `PhloInfrastructureError`

Infrastructure services (Dagster, Trino, S3, etc.) are unavailable.

**Common causes:**
- Service not running
- Connection refused
- Network issues
- Authentication failed

**Quick fix:**
```bash
# Check service status
docker ps
docker logs dagster-webserver
docker logs trino

# Restart services if needed
docker-compose restart
```

[**Full Documentation →**](./PHLO-008.md)

---

### Schema and Type Errors (PHLO-200 to PHLO-299)

Errors related to schema conversion and type handling.

#### PHLO-200: Schema Conversion Error
**Exception:** `SchemaConversionError`

Failed to convert Pandera schema to PyIceberg schema.

**Common causes:**
- Unsupported Pandera type
- Custom type without converter
- Complex nested types

**Quick fix:**
```python
# Use supported Pandera types:
# str, int, float, bool, datetime, date, bytes

class MySchema(DataFrameModel):
    id: str  # ✅ Supported
    count: int  # ✅ Supported
    value: float  # ✅ Supported
    timestamp: datetime  # ✅ Supported
```

[**Full Documentation →**](./PHLO-200.md)

---

#### PHLO-201: Type Conversion Error
**Exception:** `PhloError`

Failed to convert data types during processing.

**Common causes:**
- Invalid data format
- Type mismatch
- Encoding issues

**Quick fix:**
```python
# Explicit type conversion
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["timestamp"] = pd.to_datetime(df["timestamp"])
```

[**Full Documentation →**](./PHLO-201.md)

---

### DLT Errors (PHLO-300 to PHLO-399)

Errors specific to DLT (Data Load Tool) operations.

#### PHLO-300: DLT Pipeline Failed
**Exception:** `DLTPipelineError`

DLT pipeline execution failed.

**Common causes:**
- Source connection failed
- Data transformation error
- Destination write failed
- Pipeline configuration invalid

**Quick fix:**
```python
# Check DLT logs
import dlt

# Enable verbose logging
dlt.config.log_level = "DEBUG"
```

[**Full Documentation →**](./PHLO-300.md)

---

#### PHLO-301: DLT Source Error
**Exception:** `PhloError`

DLT source connector failed.

**Common causes:**
- Source not accessible
- Invalid credentials
- Rate limiting
- Data format unexpected

**Quick fix:**
```python
# Test source connectivity
source = my_source()
for item in source:
    print(item)
    break  # Test first item
```

[**Full Documentation →**](./PHLO-301.md)

---

### Iceberg Errors (PHLO-400 to PHLO-499)

Errors related to Apache Iceberg operations.

#### PHLO-400: Iceberg Catalog Error
**Exception:** `IcebergCatalogError`

Iceberg catalog operations failed.

**Common causes:**
- Catalog not initialized
- Connection to catalog failed
- Catalog permissions issue
- S3/backend unavailable

**Quick fix:**
```python
# Verify catalog connectivity
from pyiceberg.catalog import load_catalog

catalog = load_catalog("default")
print(f"Catalog namespaces: {catalog.list_namespaces()}")
```

[**Full Documentation →**](./PHLO-400.md)

---

#### PHLO-401: Iceberg Table Error
**Exception:** `PhloError`

Iceberg table operations failed.

**Common causes:**
- Table not found
- Schema mismatch
- Concurrent modification
- Permissions issue

**Quick fix:**
```python
# List available tables
catalog = load_catalog("default")
tables = catalog.list_tables("bronze")
print(f"Tables in bronze: {tables}")
```

[**Full Documentation →**](./PHLO-401.md)

---

#### PHLO-402: Iceberg Write Error
**Exception:** `PhloError`

Failed to write data to Iceberg table.

**Common causes:**
- Schema mismatch
- Partition spec invalid
- S3 write failed
- Insufficient permissions

**Quick fix:**
```python
# Verify schema matches table
table_schema = table.schema()
df_schema = df.dtypes

print("Table schema:", table_schema)
print("DataFrame schema:", df_schema)
```

[**Full Documentation →**](./PHLO-402.md)

---

## Error Handling Best Practices

### 1. Use Structured Error Classes

Always use Phlo exception classes with error codes:

```python
from phlo.exceptions import PhloIngestionError

raise PhloIngestionError(
    message="Failed to fetch weather data",
    suggestions=[
        "Check API connectivity",
        "Verify API credentials",
        "Review rate limits",
    ],
    cause=original_exception
)
```

### 2. Provide Actionable Suggestions

Include specific, actionable suggestions:

```python
# ❌ Bad: Generic suggestion
suggestions=["Fix the error"]

# ✅ Good: Specific actions
suggestions=[
    "Check that unique_key 'observation_id' exists in WeatherObservations schema",
    "Available fields: id, station_id, temperature, timestamp",
    "Update unique_key to match one of the available fields",
]
```

### 3. Include Context

Provide relevant context in error messages:

```python
# ❌ Bad: No context
raise PhloError("Schema mismatch")

# ✅ Good: Detailed context
raise PhloSchemaError(
    message=f"unique_key '{unique_key}' not found in {schema.__name__}",
    suggestions=suggest_similar_field_names(unique_key, available_fields)
)
```

### 4. Log Errors Appropriately

Use Dagster context for logging:

```python
@cascade_ingestion(...)
def my_asset(partition: str, context):
    try:
        data = fetch_data(partition)
        context.log.info(f"✅ Fetched {len(data)} records")
        return data
    except Exception as e:
        context.log.error(f"❌ Ingestion failed: {e}")
        raise PhloIngestionError(
            message=f"Failed to fetch data for partition {partition}",
            cause=e
        )
```

### 5. Test Error Paths

Write tests for error conditions:

```python
def test_ingestion_handles_api_failure():
    with pytest.raises(PhloIngestionError) as exc_info:
        weather_observations(partition="invalid")

    assert "API returned 404" in str(exc_info.value)
    assert exc_info.value.code == PhloErrorCode.INGESTION_FAILED
```

## Getting Help

If you encounter an error not covered in this documentation:

1. **Check Error Code:** Look up the PHLO-XXX code in the index above
2. **Read Full Documentation:** Click the link to read detailed documentation
3. **Search Issues:** Check [GitHub Issues](https://github.com/phlo/phlo/issues)
4. **Ask for Help:** Create a new issue with:
   - Error code and full error message
   - Steps to reproduce
   - Relevant code snippets
   - Environment details (OS, Python version, Phlo version)

## Contributing

Found an error not documented? Help us improve:

1. Fork the repository
2. Add documentation in `docs/errors/PHLO-XXX.md`
3. Update this index
4. Submit a pull request

Template for new error documentation:

```markdown
# PHLO-XXX: Error Name

**Error Type:** Category
**Severity:** High/Medium/Low
**Exception Class:** `ExceptionClassName`

## Description
[Clear description of when this error occurs]

## Common Causes
[List of common causes]

## Solutions
[Step-by-step solutions]

## Examples
[Code examples showing incorrect and correct usage]

## Related Errors
[Links to related error codes]

## Prevention
[Best practices to avoid this error]
```

---

**Documentation Version:** 1.0.0
**Last Updated:** 2024-01-15
**Phlo Version:** 0.1.0
