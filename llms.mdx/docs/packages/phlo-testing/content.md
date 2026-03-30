# phlo-testing (/docs/packages/phlo-testing)



Overview [#overview]

`phlo-testing` provides shared testing utilities, fixtures, and mocks for developing and testing Phlo packages. This is a development utility library, not a runtime plugin.

Installation [#installation]

```bash
pip install phlo-testing
```

Features [#features]

This package is a **utility library** with no auto-configuration:

| Feature       | Status                 |
| ------------- | ---------------------- |
| Entry Points  | None - utility library |
| Runtime Hooks | None - testing only    |

Usage [#usage]

Fixtures [#fixtures]

```python
import pytest
from phlo_testing.fixtures import (
    mock_iceberg_catalog,
    mock_nessie_client,
    mock_trino_connection,
    test_dataframe
)

def test_my_ingestion(mock_iceberg_catalog):
    # Test with mocked catalog
    catalog = mock_iceberg_catalog
    # ... test code
    pass

def test_with_nessie(mock_nessie_client):
    # Test with mocked Nessie client
    client = mock_nessie_client
    client.create_branch("test-branch")
    # ... test code
    pass
```

Test Utilities [#test-utilities]

```python
from phlo_testing.utils import (
    create_test_dataframe,
    assert_table_exists,
    assert_schema_matches,
    wait_for_service
)

# Create test data
df = create_test_dataframe(
    columns=["id", "name", "value"],
    rows=10
)

# Assert table exists
assert_table_exists("bronze.test_table")

# Assert schema matches expected
assert_schema_matches(
    table="bronze.users",
    expected_columns=["id", "name", "email"]
)

# Wait for service to be ready
wait_for_service("http://localhost:8080/health", timeout=30)
```

Mock Factories [#mock-factories]

```python
from phlo_testing.mocks import (
    MockDagsterContext,
    MockIcebergTable,
    MockTrinoResult
)

# Create mock Dagster context
context = MockDagsterContext(
    partition_key="2024-01-15"
)

# Create mock Iceberg table
table = MockIcebergTable(
    name="bronze.users",
    schema={"id": "string", "name": "string"}
)

# Create mock Trino result
result = MockTrinoResult(
    columns=["id", "name"],
    rows=[("1", "Alice"), ("2", "Bob")]
)
```

Test Marker Rules [#test-marker-rules]

```python
import pytest

@pytest.mark.unit
def test_pure_transform_logic():
    """No network, Docker, or filesystem side effects."""
    pass

@pytest.mark.integration
def test_full_pipeline():
    """Requires Docker services to be running."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Takes a long time to run."""
    pass

# Run specific markers
# pytest -m unit
# pytest -m integration
# pytest -m "not slow"
```

Use `unit` for import-only tests, pure functions, and tests that run without external services.
Use `integration` only for tests that require service discovery, Docker containers, dbt artifacts,
or other cross-package runtime wiring.

Common Test Patterns [#common-test-patterns]

Testing Ingestion [#testing-ingestion]

```python
from phlo_testing.fixtures import mock_iceberg_catalog, test_dataframe

def test_ingestion_creates_table(mock_iceberg_catalog, test_dataframe):
    # Arrange
    catalog = mock_iceberg_catalog

    # Act
    # ... run ingestion

    # Assert
    assert catalog.table_exists("bronze.my_table")
```

Contract harnesses [#contract-harnesses]

`phlo-testing` now includes profile-level harnesses for cross-package contract tests.

* `BundledStackHarness`
  Boots a real generated project against the bundled service stack using local
  workspace source.
* `NonVersionedProfileHarness`
  Boots a local DuckDB + dbt profile for fast non-versioned verification.

These harnesses are useful when unit tests are not enough and you need to prove
that the supported capability combination actually wires together correctly.

Testing Quality Checks [#testing-quality-checks]

```python
from phlo_testing.utils import create_test_dataframe
from phlo_quality.checks import null_check

def test_null_check_fails_on_nulls():
    # Create data with nulls
    df = create_test_dataframe(
        columns=["id", "name"],
        rows=10,
        null_columns=["name"]
    )

    # Run check
    check = null_check(column="name")
    result = check.execute(df)

    # Assert
    assert not result["passed"]
```

Note [#note]

This package does not register any entry points as it is intended for development and testing only.

Related Packages [#related-packages]

* [phlo-pandera](phlo-pandera.md) - Quality checks
* [phlo-dlt](phlo-dlt.md) - Data ingestion

Next Steps [#next-steps]

* [Testing Strategy Guide](../guides/testing-strategy.md) - Testing approaches
* [Operations Testing](../operations/testing.md) - Integration tests
