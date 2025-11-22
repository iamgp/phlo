# Testing Guide

A comprehensive guide to testing Cascade workflows.

## Overview

This guide covers:
- **Unit Testing**: Test schemas and business logic (fast, no Docker)
- **Integration Testing**: Test full pipelines (slower, requires Docker)
- **Best Practices**: Patterns and recommendations

**Time to write first test**: 5-10 minutes

---

## Quick Start

### 1. Copy the Test Template

```bash
cp templates/tests/test_ingestion.py tests/test_my_workflow.py
```

### 2. Run Your Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_my_workflow.py -v

# Run specific test
pytest tests/test_my_workflow.py::TestSchemaValidation::test_valid_data_passes_validation -v
```

---

## Unit Testing

Unit tests are **fast** (< 1 second), require **no Docker**, and test individual components.

### Testing Pandera Schemas

Test that your schema validates data correctly:

```python
import pytest
import pandas as pd
from cascade.schemas.weather import RawWeatherData

def test_valid_weather_data_passes_validation():
    """Test that valid weather data passes schema validation."""

    test_data = pd.DataFrame([
        {
            "city_name": "London",
            "temperature": 15.5,
            "humidity": 65,
            "timestamp": "2024-01-15T12:00:00Z",
        },
    ])

    # Should not raise
    validated = RawWeatherData.validate(test_data)
    assert len(validated) == 1


def test_invalid_temperature_fails_validation():
    """Test that invalid temperature fails validation."""

    test_data = pd.DataFrame([
        {
            "city_name": "London",
            "temperature": -200.0,  # Invalid: should be >= -100
            "humidity": 65,
            "timestamp": "2024-01-15T12:00:00Z",
        },
    ])

    # Should raise SchemaError
    with pytest.raises(Exception):
        RawWeatherData.validate(test_data)
```

### Testing Schema Configuration

Verify that your schema includes required fields:

```python
def test_schema_has_unique_key():
    """Test that unique_key field exists in schema."""

    schema_fields = RawWeatherData.to_schema().columns.keys()

    # Ensure unique_key from decorator exists in schema
    assert "timestamp" in schema_fields


def test_schema_has_required_fields():
    """Test that schema includes all required fields."""

    schema_fields = RawWeatherData.to_schema().columns.keys()

    required_fields = ["city_name", "temperature", "humidity", "timestamp"]

    for field in required_fields:
        assert field in schema_fields, f"Missing field: {field}"
```

### Testing Asset Configuration

Verify decorator parameters:

```python
import inspect
from cascade.defs.ingestion.weather.observations import weather_observations

def test_asset_has_correct_table_name():
    """Test that asset has correct table name."""

    # Asset op name should be prefixed with 'dlt_'
    assert weather_observations.op.name == "dlt_weather_observations"


def test_asset_accepts_partition_parameter():
    """Test that asset function accepts partition_date."""

    sig = inspect.signature(weather_observations.op.compute_fn)
    params = sig.parameters

    assert "partition_date" in params
```

### Testing Business Logic

Test any data transformations in your asset:

```python
def test_date_formatting():
    """Test that partition_date is formatted correctly."""

    partition_date = "2024-01-15"

    # Your formatting logic
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    assert start_time == "2024-01-15T00:00:00.000Z"
    assert end_time == "2024-01-15T23:59:59.999Z"


def test_data_filtering():
    """Test custom data filtering logic."""

    sample_data = pd.DataFrame([
        {"value": 10, "status": "active"},
        {"value": 20, "status": "inactive"},
        {"value": 30, "status": "active"},
    ])

    # Your filtering logic
    filtered = sample_data[sample_data["status"] == "active"]

    assert len(filtered) == 2
    assert filtered["value"].tolist() == [10, 30]
```

---

## Integration Testing

Integration tests require the full Docker stack and test end-to-end pipelines.

### Prerequisites

```bash
# Start Docker services
make up-core up-query

# Wait for services to be healthy
docker compose ps
```

### Testing Asset Materialization

Test full asset execution:

```python
import pytest

@pytest.mark.integration  # Mark as integration test
def test_weather_asset_materialization():
    """
    Test full weather asset materialization.

    Requires: Docker services running
    """

    # Materialize via Docker exec
    import subprocess

    result = subprocess.run([
        "docker", "exec", "dagster-webserver",
        "dagster", "asset", "materialize",
        "--select", "weather_observations",
        "--partition", "2024-01-15",
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Materialization failed: {result.stderr}"


@pytest.mark.integration
def test_data_written_to_iceberg():
    """Test that data was written to Iceberg table."""

    import trino

    conn = trino.dbapi.connect(
        host='localhost',
        port=8080,
        user='trino',
        catalog='iceberg_dev',
        schema='raw',
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM weather_observations")
    count = cursor.fetchone()[0]

    assert count > 0, "No data found in Iceberg table"
```

### Running Integration Tests

```bash
# Run only integration tests
pytest tests/ -m integration -v

# Run only unit tests (exclude integration)
pytest tests/ -m "not integration" -v

# Run with verbose output
pytest tests/ -v -s
```

---

## Current Limitations

**Note**: Cascade does not yet provide testing utilities. Until `cascade.testing` module is available, you need to:

1. **For unit tests**: Test schemas and configuration (no mocking required)
2. **For integration tests**: Use full Docker stack

**Coming soon**:
- `cascade.testing.mock_dlt_source()` - Mock DLT data sources
- `cascade.testing.mock_iceberg_catalog()` - In-memory Iceberg
- `cascade.testing.test_asset_execution()` - Test assets without Docker
- `cascade test` CLI command - Run tests from command line

---

## Test Organization

### Recommended Structure

```
tests/
├── conftest.py                     # Pytest configuration and shared fixtures
├── fixtures/                       # Test data fixtures
│   ├── weather_data.json
│   └── github_events.json
├── unit/                          # Fast tests (no Docker)
│   ├── test_schemas.py           # Schema validation tests
│   ├── test_asset_config.py      # Decorator configuration tests
│   └── test_business_logic.py    # Data transformation tests
└── integration/                   # Slow tests (require Docker)
    ├── test_weather_pipeline.py  # Full pipeline tests
    └── test_github_pipeline.py
```

### Example conftest.py

```python
"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires Docker)"
    )


@pytest.fixture
def sample_weather_data():
    """Fixture providing sample weather data."""
    return pd.DataFrame([
        {
            "city_name": "London",
            "temperature": 15.5,
            "humidity": 65,
            "timestamp": "2024-01-15T12:00:00Z",
        },
        {
            "city_name": "Paris",
            "temperature": 12.3,
            "humidity": 70,
            "timestamp": "2024-01-15T12:00:00Z",
        },
    ])


@pytest.fixture
def sample_invalid_data():
    """Fixture providing invalid weather data."""
    return pd.DataFrame([
        {
            "city_name": "London",
            "temperature": -200.0,  # Invalid
            "humidity": 150,  # Invalid
            "timestamp": "2024-01-15T12:00:00Z",
        },
    ])
```

---

## Best Practices

### 1. Test Schema First

Always test your Pandera schema before testing the full pipeline:

```python
def test_schema_validates_good_data():
    """Schema should accept valid data."""
    # Test with known good data
    pass


def test_schema_rejects_bad_data():
    """Schema should reject invalid data."""
    # Test constraint violations
    pass
```

**Why**: Schema errors are the most common issue. Catching them early saves time.

### 2. Use Descriptive Test Names

```python
# Good
def test_temperature_constraint_rejects_values_below_minus_100():
    pass

# Bad
def test_temperature():
    pass
```

**Why**: Clear names make failures easier to diagnose.

### 3. One Assertion Concept Per Test

```python
# Good
def test_temperature_field_exists():
    assert "temperature" in schema_fields

def test_temperature_has_range_constraint():
    assert schema.fields["temperature"].checks["ge"] == -100

# Bad
def test_temperature_field():
    assert "temperature" in schema_fields
    assert schema.fields["temperature"].checks["ge"] == -100
    assert schema.fields["temperature"].type == float
```

**Why**: Specific failures are easier to debug.

### 4. Use Fixtures for Test Data

```python
@pytest.fixture
def valid_weather_data():
    return pd.DataFrame([...])


def test_schema_validation(valid_weather_data):
    result = MySchema.validate(valid_weather_data)
    assert len(result) == 2
```

**Why**: Reduces duplication, makes tests more maintainable.

### 5. Mark Integration Tests

```python
@pytest.mark.integration
def test_full_pipeline():
    """Requires Docker services."""
    pass
```

**Why**: Enables running fast tests separately from slow tests.

### 6. Test Error Cases

```python
def test_handles_missing_required_field():
    """Test that missing required field raises error."""
    incomplete_data = pd.DataFrame([{"city_name": "London"}])  # Missing temperature

    with pytest.raises(Exception):
        MySchema.validate(incomplete_data)
```

**Why**: Error handling is as important as happy paths.

---

## Common Testing Patterns

### Pattern 1: Schema Validation Test

```python
def test_my_schema_validation():
    """Test schema validates expected data."""

    # Arrange
    test_data = pd.DataFrame([{...}])

    # Act
    result = MySchema.validate(test_data)

    # Assert
    assert len(result) == expected_count
    assert result["field"].dtype == expected_type
```

### Pattern 2: Constraint Violation Test

```python
def test_schema_rejects_negative_values():
    """Test that negative values are rejected."""

    invalid_data = pd.DataFrame([{"value": -10}])

    with pytest.raises(Exception) as exc_info:
        MySchema.validate(invalid_data)

    # Optionally check error message
    assert "value" in str(exc_info.value).lower()
```

### Pattern 3: Field Existence Test

```python
def test_required_fields_exist():
    """Test that all required fields are present in schema."""

    schema_fields = MySchema.to_schema().columns.keys()
    required = ["id", "timestamp", "value"]

    for field in required:
        assert field in schema_fields, f"Missing: {field}"
```

### Pattern 4: Asset Configuration Test

```python
def test_asset_decorator_configuration():
    """Test that asset decorator is configured correctly."""

    from my_asset import my_ingestion_asset

    # Check op name
    assert my_ingestion_asset.op.name == "dlt_my_table"

    # Check function signature
    import inspect
    sig = inspect.signature(my_ingestion_asset.op.compute_fn)
    assert "partition_date" in sig.parameters
```

---

## Troubleshooting

### Test Discovery Issues

**Problem**: `pytest` doesn't find your tests

**Solution**:
- Ensure test files start with `test_`
- Ensure test functions start with `test_`
- Ensure test classes start with `Test`
- Check `pytest.ini` configuration

### Import Errors

**Problem**: `ModuleNotFoundError` when running tests

**Solution**:
```bash
# Install cascade in editable mode
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH=/home/user/cascade/src:$PYTHONPATH
```

### Schema Validation Failures

**Problem**: Valid data fails schema validation

**Solution**:
- Check field types match (str vs datetime)
- Check nullable settings
- Check constraint values (ge, le, etc.)
- Use `coerce=True` in schema Config

### Integration Test Failures

**Problem**: Integration tests fail with connection errors

**Solution**:
```bash
# Check Docker services are running
docker compose ps

# Check service health
docker logs dagster-webserver
docker logs nessie
docker logs minio

# Restart services if needed
make down
make up-core up-query
```

---

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run unit tests
        run: |
          pytest tests/ -m "not integration" -v --cov=cascade

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start Docker services
        run: |
          make up-core up-query
          sleep 30  # Wait for services
      - name: Run integration tests
        run: |
          pytest tests/ -m integration -v
```

---

## Test Coverage

### Measuring Coverage

```bash
# Run tests with coverage
pytest tests/ --cov=cascade --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Coverage Goals

- **Schema validation**: 100% (easy to test)
- **Decorator configuration**: 100% (easy to test)
- **Business logic**: 90%+ (important to test)
- **Integration paths**: 70%+ (harder to test)

---

## Next Steps

1. **Start with schema tests**: Copy `templates/tests/test_ingestion.py`
2. **Add business logic tests**: Test any custom transformations
3. **Add integration tests**: Test full pipelines when ready
4. **Set up CI/CD**: Run tests on every commit
5. **Track coverage**: Aim for 80%+ overall coverage

---

## Additional Resources

- **Template**: [templates/tests/test_ingestion.py](../templates/tests/test_ingestion.py)
- **Pandera Docs**: https://pandera.readthedocs.io/
- **Pytest Docs**: https://docs.pytest.org/
- **Troubleshooting**: [Troubleshooting Guide](troubleshooting.md)

---

**Have questions?** Open a [GitHub Discussion](https://github.com/iamgp/cascade/discussions)
