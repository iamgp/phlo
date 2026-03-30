# phlo_testing (/docs/python-reference/packages/phlo-testing/phlo_testing)



Phlo Testing Infrastructure

Comprehensive testing module for validating Phlo workflows without Docker.
Provides mock implementations of Iceberg, Trino, and DLT for fast, isolated tests.

Phase 1: Core Mocks (✅ Implemented) [#phase-1-core-mocks--implemented]

MockIcebergCatalog (Task 1.1) [#mockicebergcatalog-task-11]

In-memory Iceberg catalog backed by DuckDB for fast table operations.

```python
from phlo_testing import MockIcebergCatalog

catalog = MockIcebergCatalog()
schema = pa.schema([("id", pa.int32()), ("name", pa.string())])
table = catalog.create_table("raw.users", schema=schema)
```

mock_dlt_source (Task 1.2) [#mock_dlt_source-task-12]

Mock DLT sources that return predefined data without API calls.

```python
from phlo_testing import mock_dlt_source

data = [\{"id": 1, "name": "Alice"\}]
source = mock_dlt_source(data, resource_name="users")
```

Phase 2: Execution & Resources (✅ Implemented) [#phase-2-execution--resources--implemented]

test_asset_execution (Task 1.3) [#test_asset_execution-task-13]

Execute assets with mocked dependencies and capture results.

```python
from phlo_testing import test_asset_execution

result = test_asset_execution(
    my_asset,
    partition="2024-01-01",
    mock_data=[\{"id": 1, "name": "Alice"\}],
)
assert result.success
assert len(result.data) == 1
```

MockTrinoResource (Task 1.4) [#mocktrinoresource-task-14]

Mock Trino resource backed by DuckDB for SQL testing.

```python
from phlo_testing import MockTrinoResource

trino = MockTrinoResource()
cursor = trino.cursor()
cursor.execute("SELECT * FROM users")
```

pytest Fixtures (Task 1.5) [#pytest-fixtures-task-15]

Reusable fixtures for common test scenarios.

```python
def test_my_asset(mock_iceberg_catalog, mock_trino, sample_partition_date):
    # Fixtures automatically provided
    pass
```

Local Test Mode (Task 1.6) [#local-test-mode-task-16]

Enable `phlo test --local` without Docker.

```python
from phlo_testing import local_test_mode

with local_test_mode():
    # All resources are mocked automatically
    pass
```

Quick Start [#quick-start]

1\. Basic Asset Test [#1-basic-asset-test]

```python
from phlo_testing import test_asset_execution, mock_dlt_source

def test_ingestion_asset():
    data = [\{"id": 1, "value": 42\}]
    result = test_asset_execution(
        my_ingestion_asset,
        partition="2024-01-01",
        mock_data=data,
    )
    assert result.success
    assert len(result.data) == 1
```

2\. Using Fixtures [#2-using-fixtures]

```python
def test_with_fixtures(mock_iceberg_catalog, sample_partition_date):
    schema = create_schema()
    table = mock_iceberg_catalog.create_table(
        "raw.test",
        schema=schema,
    )
    # Use in your test
```

3\. Fixture Recording [#3-fixture-recording]

```python
from phlo_testing import FixtureRecorder

recorder = FixtureRecorder()
data = recorder.record_dlt_source(
    "users",
    my_api_fetch_function,
)
# Data is saved for replay in tests
```

Performance [#performance]

* MockIcebergCatalog: \< 100ms per operation
* MockTrinoResource: \< 10ms per query
* test\_asset\_execution: \< 1 second typical
* Full test suite: \< 5 seconds

Features [#features]

✅ Drop-in replacements for production resources
✅ DuckDB-backed for compatibility with Trino SQL
✅ Automatic resource cleanup
✅ Fixture recording and playback
✅ Context manager and fixture support
✅ Error injection for testing failure paths
✅ Session and function-scoped fixtures

Modules [#modules]

* `mock_iceberg.py` - MockIcebergCatalog and table operations
* `mock_dlt.py` - Mock DLT sources and pipelines
* `mock_trino.py` - MockTrinoResource and SQL execution
* `execution.py` - Asset execution with mocked dependencies
* `fixtures.py` - pytest fixtures for common scenarios
* `local_mode.py` - Local test mode with fixture recording

Testing Guide [#testing-guide]

For comprehensive testing patterns and best practices, see:
`docs/TESTING_GUIDE.md`

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;missing_exports&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;[]&#x22;" />

<PyAttribute name="&#x22;fixture&#x22;" type="null" value="&#x22;getattr(_fixtures_module, _fixture_name, _MISSING)&#x22;" />

<PyAttribute name="&#x22;missing&#x22;" type="null" value="&#x22;', '.join(missing_exports)&#x22;" />

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['MockIcebergCatalog', 'MockTable', 'MockTableScan', 'MockDLTResource', 'MockDLTSource', 'mock_dlt_source', 'mock_dlt_source_multi', 'mock_dlt_source_with_error', 'mock_dlt_pipeline', 'create_mock_dlt_dataframe', 'MockDLTError', 'MockTrinoResource', 'MockConnection', 'MockCursor', 'test_asset_execution', 'test_asset_with_catalog', 'test_asset_with_trino', 'AssetTestResult', 'MockAssetContext', 'TestAssetExecutor', 'LocalTestMode', 'local_test_mode', 'local_test', 'FixtureRecorder', 'is_local_test_mode', 'enable_local_test_mode', 'disable_local_test_mode', 'set_fixture_dir', 'get_fixture_dir', 'CONFTEST_TEMPLATE', 'get_conftest_template', 'MockHookBus', 'capture_events', 'sample_ingestion_event', 'sample_quality_event', 'sample_transform_event', 'sample_publish_event', 'sample_lineage_event', 'sample_telemetry_event', 'sample_service_event', 'BUNDLED_STACK_CORE_SERVICES', 'BUNDLED_STACK_DEV_PACKAGES', 'BundledStackHarness', 'BundledStackPorts', 'bootstrap_bundled_stack_harness', 'build_bundled_stack_env_updates', 'bundled_stack_contract_enabled', 'keep_bundled_stack_running', 'NonVersionedProfileHarness', 'bootstrap_non_versioned_profile_harness']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.3'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_iceberg&#x22;" title="&#x22;mock_iceberg&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/utils&#x22;" title="&#x22;utils&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/non_versioned_profile_harness&#x22;" title="&#x22;non_versioned_profile_harness&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders&#x22;" title="&#x22;placeholders&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt&#x22;" title="&#x22;mock_dlt&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/fixtures&#x22;" title="&#x22;fixtures&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/execution&#x22;" title="&#x22;execution&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode&#x22;" title="&#x22;local_mode&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/profile_harness&#x22;" title="&#x22;profile_harness&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/conftest_template&#x22;" title="&#x22;conftest_template&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/hooks&#x22;" title="&#x22;hooks&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_trino&#x22;" title="&#x22;mock_trino&#x22;" />
    </Cards>
  </Tab>
</Tabs>
