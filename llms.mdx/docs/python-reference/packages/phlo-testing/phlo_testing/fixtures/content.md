# fixtures (/docs/python-reference/packages/phlo-testing/phlo_testing/fixtures)



Pytest fixtures for testing Phlo assets and workflows.

Provides reusable fixtures for common test scenarios including mock resources,
test data, and temporary directories.

Example:

> > > def test\_my\_asset(mock\_iceberg\_catalog, sample\_partition\_date):
> > > ...     # Use fixtures automatically
> > > ...     pass

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;mock_iceberg_catalog&#x22;" type="&#x22;() -> Iterator[MockIcebergCatalog]&#x22;">
      Provide a fresh MockIcebergCatalog for each test.

      Fixture is function-scoped and auto-cleaned up after test.

      Example:

      > > > def test\_with\_catalog(mock\_iceberg\_catalog):
      > > > ...     table = mock\_iceberg\_catalog.create\_table(
      > > > ...         "raw\.users",
      > > > ...         schema=get\_schema(),
      > > > ...     )

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_iceberg_catalog() -> Iterator[MockIcebergCatalog]:
            """
            Provide a fresh MockIcebergCatalog for each test.

            Fixture is function-scoped and auto-cleaned up after test.

            Example:
                >>> def test_with_catalog(mock_iceberg_catalog):
                ...     table = mock_iceberg_catalog.create_table(
                ...         "raw.users",
                ...         schema=get_schema(),
                ...     )

            """
            catalog = MockIcebergCatalog()
            yield catalog
            catalog.close()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[phlo_testing.mock_iceberg.MockIcebergCatalog]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;mock_trino&#x22;" type="&#x22;() -> Iterator[MockTrinoResource]&#x22;">
      Provide a fresh MockTrinoResource for each test.

      Fixture is function-scoped and auto-cleaned up after test.

      Example:

      > > > def test\_with\_trino(mock\_trino):
      > > > ...     cursor = mock\_trino.cursor()
      > > > ...     cursor.execute("SELECT 1 as id")

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_trino() -> Iterator[MockTrinoResource]:
            """
            Provide a fresh MockTrinoResource for each test.

            Fixture is function-scoped and auto-cleaned up after test.

            Example:
                >>> def test_with_trino(mock_trino):
                ...     cursor = mock_trino.cursor()
                ...     cursor.execute("SELECT 1 as id")

            """
            trino = MockTrinoResource()
            yield trino
            trino.close()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[phlo_testing.mock_trino.MockTrinoResource]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;mock_asset_context&#x22;" type="&#x22;() -> Iterator[MockAssetContext]&#x22;">
      Provide a fresh MockAssetContext for each test.

      Includes mock Iceberg and Trino resources plus logging capture.

      Example:

      > > > def test\_with\_context(mock\_asset\_context):
      > > > ...     context.log("test message")
      > > > ...     assert "test message" in context.logs

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_asset_context() -> Iterator[MockAssetContext]:
            """
            Provide a fresh MockAssetContext for each test.

            Includes mock Iceberg and Trino resources plus logging capture.

            Example:
                >>> def test_with_context(mock_asset_context):
                ...     context.log("test message")
                ...     assert "test message" in context.logs

            """
            context = MockAssetContext()
            yield context
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[phlo_testing.execution.MockAssetContext]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;mock_hook_bus&#x22;" type="&#x22;() -> MockHookBus&#x22;">
      Provide a mock hook bus without plugin discovery.

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_hook_bus() -> MockHookBus:
            """Provide a mock hook bus without plugin discovery."""
            return MockHookBus()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_testing.hooks.MockHookBus&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;mock_resources&#x22;" type="&#x22;(mock_iceberg_catalog, mock_trino) -> dict[str, Any]&#x22;">
      Provide all mock resources in a dict.

      Useful for passing to functions that need multiple resources.

      Example:

      > > > def test\_with\_resources(mock\_resources):
      > > > ...     table\_store = mock\_resources\["table\_store"]
      > > > ...     trino = mock\_resources\["trino"]

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_resources(
            mock_iceberg_catalog: MockIcebergCatalog,
            mock_trino: MockTrinoResource,
        ) -> dict[str, Any]:
            """
            Provide all mock resources in a dict.

            Useful for passing to functions that need multiple resources.

            Example:
                >>> def test_with_resources(mock_resources):
                ...     table_store = mock_resources["table_store"]
                ...     trino = mock_resources["trino"]

            """
            return {
                "table_store": mock_iceberg_catalog,
                "trino": mock_trino,
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;mock_iceberg_catalog&#x22;" type="&#x22;MockIcebergCatalog&#x22;" value="null" />

        <PyParameter name="&#x22;mock_trino&#x22;" type="&#x22;MockTrinoResource&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;sample_partition_date&#x22;" type="&#x22;() -> str&#x22;">
      Provide a standard partition date for tests.

      Returns ISO format date string (e.g., "2024-01-15").

      Example:

      > > > def test\_asset(sample\_partition\_date):
      > > > ...     assert sample\_partition\_date == "2024-01-15"

      <PySourceCode>
        ```python
        @pytest.fixture
        def sample_partition_date() -> str:
            """
            Provide a standard partition date for tests.

            Returns ISO format date string (e.g., "2024-01-15").

            Example:
                >>> def test_asset(sample_partition_date):
                ...     assert sample_partition_date == "2024-01-15"

            """
            return "2024-01-15"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;sample_partition_range&#x22;" type="&#x22;() -> tuple[str, str]&#x22;">
      Provide a range of partition dates.

      Returns tuple of (start\_date, end\_date) in ISO format.

      Example:

      > > > def test\_backfill(sample\_partition\_range):
      > > > ...     start, end = sample\_partition\_range
      > > > ...     # start = "2024-01-01"
      > > > ...     # end = "2024-01-31"

      <PySourceCode>
        ```python
        @pytest.fixture
        def sample_partition_range() -> tuple[str, str]:
            """
            Provide a range of partition dates.

            Returns tuple of (start_date, end_date) in ISO format.

            Example:
                >>> def test_backfill(sample_partition_range):
                ...     start, end = sample_partition_range
                ...     # start = "2024-01-01"
                ...     # end = "2024-01-31"

            """
            start = "2024-01-01"
            end = "2024-01-31"
            return (start, end)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;tuple[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;sample_dlt_data&#x22;" type="&#x22;() -> list[dict[str, Any]]&#x22;">
      Provide sample DLT source data.

      Returns list of test records.

      Example:

      > > > def test\_ingestion(sample\_dlt\_data):
      > > > ...     source = mock\_dlt\_source(sample\_dlt\_data)

      <PySourceCode>
        ```python
        @pytest.fixture
        def sample_dlt_data() -> list[dict[str, Any]]:
            """
            Provide sample DLT source data.

            Returns list of test records.

            Example:
                >>> def test_ingestion(sample_dlt_data):
                ...     source = mock_dlt_source(sample_dlt_data)

            """
            return [
                {
                    "id": 1,
                    "name": "Alice",
                    "email": "alice@example.com",
                    "created_at": "2024-01-15T10:00:00Z",
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "email": "bob@example.com",
                    "created_at": "2024-01-15T11:00:00Z",
                },
                {
                    "id": 3,
                    "name": "Charlie",
                    "email": "charlie@example.com",
                    "created_at": "2024-01-15T12:00:00Z",
                },
            ]
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;sample_dataframe&#x22;" type="&#x22;() -> pd.DataFrame&#x22;">
      Provide a sample DataFrame for testing.

      Example:

      > > > def test\_transform(sample\_dataframe):
      > > > ...     assert len(sample\_dataframe) == 3

      <PySourceCode>
        ```python
        @pytest.fixture
        def sample_dataframe() -> pd.DataFrame:
            """
            Provide a sample DataFrame for testing.

            Example:
                >>> def test_transform(sample_dataframe):
                ...     assert len(sample_dataframe) == 3

            """
            return pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "name": ["Alice", "Bob", "Charlie"],
                    "value": [100.5, 200.75, 150.25],
                    "date": pd.date_range("2024-01-01", periods=3),
                }
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pandas.pandas.DataFrame&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;mock_dlt_source_fixture&#x22;" type="&#x22;(sample_dlt_data) -> MockDLTResource&#x22;">
      Provide a mock DLT source with sample data.

      Example:

      > > > def test\_with\_source(mock\_dlt\_source\_fixture):
      > > > ...     for record in mock\_dlt\_source\_fixture:
      > > > ...         # Process record

      <PySourceCode>
        ```python
        @pytest.fixture
        def mock_dlt_source_fixture(sample_dlt_data: list[dict]) -> MockDLTResource:
            """
            Provide a mock DLT source with sample data.

            Example:
                >>> def test_with_source(mock_dlt_source_fixture):
                ...     for record in mock_dlt_source_fixture:
                ...         # Process record

            """
            return mock_dlt_source(sample_dlt_data, resource_name="test_data")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;sample_dlt_data&#x22;" type="&#x22;list[dict]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;temp_staging_dir&#x22;" type="&#x22;() -> Iterator[Path]&#x22;">
      Provide a temporary directory for test files.

      Auto-cleaned up after test.

      Example:

      > > > def test\_with\_temp\_dir(temp\_staging\_dir):
      > > > ...     parquet\_file = temp\_staging\_dir / "data.parquet"
      > > > ...     df.to\_parquet(parquet\_file)

      <PySourceCode>
        ```python
        @pytest.fixture
        def temp_staging_dir() -> Iterator[Path]:
            """
            Provide a temporary directory for test files.

            Auto-cleaned up after test.

            Example:
                >>> def test_with_temp_dir(temp_staging_dir):
                ...     parquet_file = temp_staging_dir / "data.parquet"
                ...     df.to_parquet(parquet_file)

            """
            with tempfile.TemporaryDirectory() as tmpdir:
                yield Path(tmpdir)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[pathlib.Path]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;test_data_dir&#x22;" type="&#x22;() -> Path&#x22;">
      Provide path to test data directory.

      Looks for `tests/fixtures/data/` relative to project root.

      Example:

      > > > def test\_with\_data\_dir(test\_data\_dir):
      > > > ...     data\_file = test\_data\_dir / "users.json"

      <PySourceCode>
        ```python
        @pytest.fixture
        def test_data_dir() -> Path:
            """
            Provide path to test data directory.

            Looks for `tests/fixtures/data/` relative to project root.

            Example:
                >>> def test_with_data_dir(test_data_dir):
                ...     data_file = test_data_dir / "users.json"

            """
            # Find project root by looking for pyproject.toml
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    return current / "tests" / "fixtures" / "data"
                current = current.parent

            # Fallback to temp dir if not found
            return Path(tempfile.gettempdir()) / "test_data"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;setup_test_catalog&#x22;" type="&#x22;(mock_iceberg_catalog, sample_dataframe) -> MockIcebergCatalog&#x22;">
      Provide a pre-populated test catalog.

      Creates sample tables in the catalog.

      Example:

      > > > def test\_with\_setup\_catalog(setup\_test\_catalog):
      > > > ...     table = setup\_test\_catalog.load\_table("raw\.users")

      <PySourceCode>
        ```python
        @pytest.fixture
        def setup_test_catalog(
            mock_iceberg_catalog: MockIcebergCatalog,
            sample_dataframe: pd.DataFrame,
        ) -> MockIcebergCatalog:
            """
            Provide a pre-populated test catalog.

            Creates sample tables in the catalog.

            Example:
                >>> def test_with_setup_catalog(setup_test_catalog):
                ...     table = setup_test_catalog.load_table("raw.users")

            """
            from pyiceberg.schema import Schema
            from pyiceberg.types import DoubleType, IntegerType, NestedField, StringType

            # Create sample table
            schema = Schema(
                NestedField(field_id=1, name="id", type=IntegerType(), required=True),
                NestedField(field_id=2, name="name", type=StringType(), required=True),
                NestedField(field_id=3, name="value", type=DoubleType(), required=False),
            )

            table = mock_iceberg_catalog.create_table("raw.test_data", schema=schema)
            table.append(sample_dataframe)

            return mock_iceberg_catalog
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;mock_iceberg_catalog&#x22;" type="&#x22;MockIcebergCatalog&#x22;" value="null" />

        <PyParameter name="&#x22;sample_dataframe&#x22;" type="&#x22;pd.DataFrame&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_iceberg.MockIcebergCatalog&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;setup_test_trino&#x22;" type="&#x22;(mock_trino, sample_dataframe) -> MockTrinoResource&#x22;">
      Provide a pre-populated Trino resource.

      Loads sample tables into Trino.

      Example:

      > > > def test\_with\_setup\_trino(setup\_test\_trino):
      > > > ...     cursor = setup\_test\_trino.cursor()
      > > > ...     cursor.execute("SELECT \* FROM test.sample\_data")

      <PySourceCode>
        ```python
        @pytest.fixture
        def setup_test_trino(
            mock_trino: MockTrinoResource,
            sample_dataframe: pd.DataFrame,
        ) -> MockTrinoResource:
            """
            Provide a pre-populated Trino resource.

            Loads sample tables into Trino.

            Example:
                >>> def test_with_setup_trino(setup_test_trino):
                ...     cursor = setup_test_trino.cursor()
                ...     cursor.execute("SELECT * FROM test.sample_data")

            """
            mock_trino.load_table("test.sample_data", sample_dataframe)
            return mock_trino
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;mock_trino&#x22;" type="&#x22;MockTrinoResource&#x22;" value="null" />

        <PyParameter name="&#x22;sample_dataframe&#x22;" type="&#x22;pd.DataFrame&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_trino.MockTrinoResource&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;load_json_fixture&#x22;" type="&#x22;(test_data_dir) -> Callable[[str], Any]&#x22;">
      Provide helper to load JSON fixture files.

      Example:

      > > > def test\_with\_json(load\_json\_fixture):
      > > > ...     data = load\_json\_fixture("users.json")

      <PySourceCode>
        ```python
        @pytest.fixture
        def load_json_fixture(test_data_dir: Path) -> Callable[[str], Any]:
            """
            Provide helper to load JSON fixture files.

            Example:
                >>> def test_with_json(load_json_fixture):
                ...     data = load_json_fixture("users.json")

            """

            def _load_json(filename: str) -> Any:
                filepath = test_data_dir / filename
                if not filepath.exists():
                    raise FileNotFoundError(f"Fixture not found: {filepath}")

                with open(filepath) as f:
                    return json.load(f)

            return _load_json
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_data_dir&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Callable[[str], typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;load_csv_fixture&#x22;" type="&#x22;(test_data_dir) -> Callable[[str], pd.DataFrame]&#x22;">
      Provide helper to load CSV fixture files.

      Example:

      > > > def test\_with\_csv(load\_csv\_fixture):
      > > > ...     df = load\_csv\_fixture("users.csv")

      <PySourceCode>
        ```python
        @pytest.fixture
        def load_csv_fixture(test_data_dir: Path) -> Callable[[str], pd.DataFrame]:
            """
            Provide helper to load CSV fixture files.

            Example:
                >>> def test_with_csv(load_csv_fixture):
                ...     df = load_csv_fixture("users.csv")

            """

            def _load_csv(filename: str) -> pd.DataFrame:
                filepath = test_data_dir / filename
                if not filepath.exists():
                    raise FileNotFoundError(f"Fixture not found: {filepath}")

                return pd.read_csv(filepath)

            return _load_csv
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_data_dir&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Callable[[str], pandas.pandas.DataFrame]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;test_config&#x22;" type="&#x22;() -> dict[str, Any]&#x22;">
      Provide test configuration overrides.

      Returns dict with test-specific config values.

      Example:

      > > > def test\_with\_config(test\_config, monkeypatch):
      > > > ...     monkeypatch.setenv("PHLO\_ENV", "test")

      <PySourceCode>
        ```python
        @pytest.fixture
        def test_config() -> dict[str, Any]:
            """
            Provide test configuration overrides.

            Returns dict with test-specific config values.

            Example:
                >>> def test_with_config(test_config, monkeypatch):
                ...     monkeypatch.setenv("PHLO_ENV", "test")

            """
            return {
                "environment": "test",
                "log_level": "DEBUG",
                "parallel_workers": 1,
            }
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;session_temp_dir&#x22;" type="&#x22;() -> Iterator[Path]&#x22;">
      Provide a temporary directory for the entire test session.

      Useful for shared test data.

      Example:

      > > > def test\_with\_session\_dir(session\_temp\_dir):
      > > > ...     # Shared across all tests in session

      <PySourceCode>
        ```python
        @pytest.fixture(scope="session")
        def session_temp_dir() -> Iterator[Path]:
            """
            Provide a temporary directory for the entire test session.

            Useful for shared test data.

            Example:
                >>> def test_with_session_dir(session_temp_dir):
                ...     # Shared across all tests in session

            """
            with tempfile.TemporaryDirectory() as tmpdir:
                yield Path(tmpdir)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[pathlib.Path]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;session_catalog&#x22;" type="&#x22;() -> Iterator[MockIcebergCatalog]&#x22;">
      Provide a catalog shared across all tests in session.

      Use carefully - tests should clean up their own tables.

      Example:

      > > > def test\_with\_session\_catalog(session\_catalog):
      > > > ...     # Shared across all tests

      <PySourceCode>
        ```python
        @pytest.fixture(scope="session")
        def session_catalog() -> Iterator[MockIcebergCatalog]:
            """
            Provide a catalog shared across all tests in session.

            Use carefully - tests should clean up their own tables.

            Example:
                >>> def test_with_session_catalog(session_catalog):
                ...     # Shared across all tests

            """
            catalog = MockIcebergCatalog()
            yield catalog
            catalog.close()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Iterator[phlo_testing.mock_iceberg.MockIcebergCatalog]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;create_partition_dates&#x22;" type="&#x22;(start, end, step_days=1) -> list[str]&#x22;">
      Create list of partition dates for parametrized tests.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > dates = create\_partition\_dates("2024-01-01", "2024-01-31", step\_days=7)
        > > >
        > > > \["2024-01-01", "2024-01-08", "2024-01-15", ...] [#2024-01-01-2024-01-08-2024-01-15-]
      </Callout>

      <PySourceCode>
        ```python
        def create_partition_dates(start: str, end: str, step_days: int = 1) -> list[str]:
            """
            Create list of partition dates for parametrized tests.

            Args:
                start: Start date (ISO format)
                end: End date (ISO format)
                step_days: Days between partitions

            Returns:
                List of date strings

            Example:
                >>> dates = create_partition_dates("2024-01-01", "2024-01-31", step_days=7)
                >>> # ["2024-01-01", "2024-01-08", "2024-01-15", ...]

            """
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)

            dates = []
            current = start_dt

            while current <= end_dt:
                dates.append(current.isoformat()[:10])
                current += timedelta(days=step_days)

            return dates
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;start&#x22;" type="&#x22;str&#x22;" value="undefined">
          Start date (ISO format)
        </PyParameter>

        <PyParameter name="&#x22;end&#x22;" type="&#x22;str&#x22;" value="undefined">
          End date (ISO format)
        </PyParameter>

        <PyParameter name="&#x22;step_days&#x22;" type="&#x22;int&#x22;" value="&#x22;1&#x22;">
          Days between partitions
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of date strings
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;conftest_template&#x22;" type="&#x22;() -> str&#x22;">
      Get template for conftest.py file.

      Provides a ready-to-use conftest.py for new test directories.

      <PySourceCode>
        ```python
        @pytest.fixture
        def conftest_template() -> str:
            """
            Get template for conftest.py file.

            Provides a ready-to-use conftest.py for new test directories.

            Returns:
                String content for conftest.py

            """
            return get_conftest_template()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        String content for conftest.py
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
