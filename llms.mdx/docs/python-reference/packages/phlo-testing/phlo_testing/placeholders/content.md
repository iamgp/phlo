# placeholders (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders)



Testing utilities and mock implementations for Phlo workflows.

Provides comprehensive testing utilities including mock DLT sources,
mock Iceberg catalog backed by DuckDB, fixture management, and test
execution helpers for validating Phlo workflows without Docker.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;ICEBERG_DEPS_AVAILABLE&#x22;" type="null" value="&#x22;True&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MockDLTSource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockDLTSource&#x22;" />

      <Card title="&#x22;MockIcebergTable&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockIcebergTable&#x22;" />

      <Card title="&#x22;MockTableScan&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockTableScan&#x22;" />

      <Card title="&#x22;MockIcebergCatalog&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockIcebergCatalog&#x22;" />

      <Card title="&#x22;TestAssetResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/TestAssetResult&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;mock_dlt_source&#x22;" type="&#x22;(data, resource_name='mock_resource')&#x22;">
      Context manager for mocking DLT sources.

      Provides a convenient way to use MockDLTSource as a context manager
      for isolated testing scenarios.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > test\_data = \[\{"id": "1", "value": 42}]
        > > > with mock\_dlt\_source(data=test\_data, resource\_name="test") as source:
        > > > ...     result = list(source)
        > > > ...     assert len(result) == 1
      </Callout>

      <PySourceCode>
        ```python
        @contextmanager
        def mock_dlt_source(
            data: Union[List[Dict[str, Any]], pd.DataFrame],
            resource_name: str = "mock_resource",
        ):
            """Context manager for mocking DLT sources.

            Provides a convenient way to use MockDLTSource as a context manager
            for isolated testing scenarios.

            Args:
                data: Either list of dictionaries or pandas DataFrame containing
                    test data records.
                resource_name: Name of the mock DLT resource.

            Yields:
                MockDLTSource instance configured with the provided data.

            Example:
                >>> test_data = [{"id": "1", "value": 42}]
                >>> with mock_dlt_source(data=test_data, resource_name="test") as source:
                ...     result = list(source)
                ...     assert len(result) == 1

            """
            source = MockDLTSource(data, resource_name)
            try:
                yield source
            finally:
                pass
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;Union[List[Dict[str, Any]], pd.DataFrame]&#x22;" value="undefined">
          Either list of dictionaries or pandas DataFrame containing
          test data records.
        </PyParameter>

        <PyParameter name="&#x22;resource_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'mock_resource'&#x22;">
          Name of the mock DLT resource.
        </PyParameter>
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;mock_iceberg_catalog&#x22;" type="&#x22;()&#x22;">
      Context manager for mocking Iceberg catalog.

      Creates an in-memory Iceberg catalog backed by DuckDB.
      Perfect for fast unit tests without Docker infrastructure.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_iceberg.schema\_conversion import pandera\_to\_iceberg
        > > > from workflows.schemas.weather import RawWeatherData
        > > > iceberg\_schema = pandera\_to\_iceberg(RawWeatherData)
        > > > with mock\_iceberg\_catalog() as catalog:
        > > > ...     table = catalog.create\_table("raw\.weather", schema=iceberg\_schema)
        > > > ...     test\_data = pd.DataFrame(\[
        > > > ...         \{"city": "London", "temp": 15.5, "timestamp": "2024-01-15"},
        > > > ...     ])
        > > > ...     validated = RawWeatherData.validate(test\_data)
        > > > ...     table.append(validated)
        > > > ...     result = table.scan().to\_pandas()
        > > > ...     assert len(result) == 1
      </Callout>

      Status: Fully implemented

      <PySourceCode>
        ```python
        @contextmanager
        def mock_iceberg_catalog():
            """Context manager for mocking Iceberg catalog.

            Creates an in-memory Iceberg catalog backed by DuckDB.
            Perfect for fast unit tests without Docker infrastructure.

            Yields:
                MockIcebergCatalog instance.

            Example:
                >>> from phlo_iceberg.schema_conversion import pandera_to_iceberg
                >>> from workflows.schemas.weather import RawWeatherData
                >>> iceberg_schema = pandera_to_iceberg(RawWeatherData)
                >>> with mock_iceberg_catalog() as catalog:
                ...     table = catalog.create_table("raw.weather", schema=iceberg_schema)
                ...     test_data = pd.DataFrame([
                ...         {"city": "London", "temp": 15.5, "timestamp": "2024-01-15"},
                ...     ])
                ...     validated = RawWeatherData.validate(test_data)
                ...     table.append(validated)
                ...     result = table.scan().to_pandas()
                ...     assert len(result) == 1

            Status: Fully implemented

            """
            catalog = MockIcebergCatalog()
            try:
                yield catalog
            finally:
                catalog.close()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;test_asset_execution&#x22;" type="&#x22;(asset_fn, partition, mock_data=None, validation_schema=None) -> TestAssetResult&#x22;">
      Test asset execution with mocked dependencies.

      Executes an asset function with mock data and optional schema validation.
      Does not require Docker or Dagster infrastructure.

      This is a simplified testing helper that:

      * Executes the asset function directly (bypasses Dagster)
      * Uses MockDLTSource if mock\_data provided
      * Validates with Pandera schema if provided
      * Returns success/failure with data

      Limitations:

      * Does not execute within Dagster context
      * Does not write to actual Iceberg tables
      * Does not test Dagster-specific features (retries, metadata, etc.)
      * Good for testing asset logic, not full pipeline

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Test with mock data:

        > > > def my\_asset\_logic(partition\_date: str):
        > > > ...     return rest\_api(\{...})  # Returns DLT source
        > > > test\_data = \[\{"id": "1", "city": "London", "temp": 15.5}]
        > > > result = test\_asset\_execution(
        > > > ...     asset\_fn=my\_asset\_logic,
        > > > ...     partition="2024-01-15",
        > > > ...     mock\_data=test\_data,
        > > > ...     validation\_schema=RawWeatherData,
        > > > ... )
        > > > assert result.success
        > > > assert len(result.data) == 1

        Test actual API call:

        > > > result = test\_asset\_execution(
        > > > ...     asset\_fn=my\_asset\_logic,
        > > > ...     partition="2024-01-15",
        > > > ...     validation\_schema=RawWeatherData,
        > > > ... )
        > > > assert result.success
        > > > assert len(result.data) > 0
      </Callout>

      Status: Implemented (basic version)

      <PySourceCode>
        ```python
        def test_asset_execution(
            asset_fn: Callable[..., Any],
            partition: str,
            mock_data: Optional[Union[List[Dict[str, Any]], pd.DataFrame]] = None,
            validation_schema: Optional[Any] = None,
        ) -> TestAssetResult:
            """Test asset execution with mocked dependencies.

            Executes an asset function with mock data and optional schema validation.
            Does not require Docker or Dagster infrastructure.

            This is a simplified testing helper that:
            - Executes the asset function directly (bypasses Dagster)
            - Uses MockDLTSource if mock_data provided
            - Validates with Pandera schema if provided
            - Returns success/failure with data

            Limitations:
            - Does not execute within Dagster context
            - Does not write to actual Iceberg tables
            - Does not test Dagster-specific features (retries, metadata, etc.)
            - Good for testing asset logic, not full pipeline

            Args:
                asset_fn: The asset function to test (the original function, NOT decorated).
                partition: Partition date string (e.g., "2024-01-15").
                mock_data: Test data to use. If None, asset must fetch real data.
                validation_schema: Pandera schema for validation (optional).

            Returns:
                TestAssetResult with success status, data, and any errors.

            Example:
                Test with mock data:

                >>> def my_asset_logic(partition_date: str):
                ...     return rest_api({...})  # Returns DLT source
                >>> test_data = [{"id": "1", "city": "London", "temp": 15.5}]
                >>> result = test_asset_execution(
                ...     asset_fn=my_asset_logic,
                ...     partition="2024-01-15",
                ...     mock_data=test_data,
                ...     validation_schema=RawWeatherData,
                ... )
                >>> assert result.success
                >>> assert len(result.data) == 1

                Test actual API call:

                >>> result = test_asset_execution(
                ...     asset_fn=my_asset_logic,
                ...     partition="2024-01-15",
                ...     validation_schema=RawWeatherData,
                ... )
                >>> assert result.success
                >>> assert len(result.data) > 0

            Status: Implemented (basic version)

            """
            try:
                # Execute asset function
                if mock_data is not None:
                    # Use mock data - wrap in MockDLTSource if it's not already a source
                    if isinstance(mock_data, (list, pd.DataFrame)):
                        source = MockDLTSource(data=mock_data)
                        # Asset functions typically return a DLT source, not the data
                        # So we simulate this by returning the mock source
                        result_source = source
                    else:
                        result_source = mock_data
                else:
                    # No mock data - execute actual asset function
                    result_source = asset_fn(partition)

                # Convert source to DataFrame
                if hasattr(result_source, "to_pandas"):
                    df = result_source.to_pandas()
                elif hasattr(result_source, "__iter__"):
                    # DLT source is iterable
                    data_list = list(result_source)
                    df = pd.DataFrame(data_list)
                elif isinstance(result_source, pd.DataFrame):
                    df = result_source
                else:
                    raise ValueError(
                        f"Asset function returned unexpected type: {type(result_source)}. "
                        "Expected DLT source, DataFrame, or iterable."
                    )

                # Validate with schema if provided
                if validation_schema is not None:
                    try:
                        df = validation_schema.validate(df)
                        metadata = {"validation": "passed"}
                    except Exception as e:
                        logger.debug(
                            "testing_asset_validation_failed",
                            asset_name=getattr(asset_fn, "__name__", str(asset_fn)),
                            partition=partition,
                            exc_info=True,
                        )
                        return TestAssetResult(
                            success=False,
                            data=df,
                            error=e,
                            metadata={"validation": "failed", "error": str(e)},
                        )
                else:
                    metadata = {"validation": "skipped"}

                return TestAssetResult(
                    success=True,
                    data=df,
                    error=None,
                    metadata=metadata,
                )

            except Exception as e:
                logger.debug(
                    "testing_asset_execution_failed",
                    asset_name=getattr(asset_fn, "__name__", str(asset_fn)),
                    partition=partition,
                    exc_info=True,
                )
                return TestAssetResult(
                    success=False,
                    data=None,
                    error=e,
                    metadata={"error": str(e)},
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable[..., Any]&#x22;" value="undefined">
          The asset function to test (the original function, NOT decorated).
        </PyParameter>

        <PyParameter name="&#x22;partition&#x22;" type="&#x22;str&#x22;" value="undefined">
          Partition date string (e.g., "2024-01-15").
        </PyParameter>

        <PyParameter name="&#x22;mock_data&#x22;" type="&#x22;Optional[Union[List[Dict[str, Any]], pd.DataFrame]]&#x22;" value="&#x22;None&#x22;">
          Test data to use. If None, asset must fetch real data.
        </PyParameter>

        <PyParameter name="&#x22;validation_schema&#x22;" type="&#x22;Optional[Any]&#x22;" value="&#x22;None&#x22;">
          Pandera schema for validation (optional).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.placeholders.TestAssetResult&#x22;">
        TestAssetResult with success status, data, and any errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;load_fixture&#x22;" type="&#x22;(path) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]&#x22;">
      Load test fixture from file.

      Supports JSON, CSV, and Parquet files. Automatically detects format
      from file extension.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > Load JSON fixture [#load-json-fixture]
        > > >
        > > > test\_data = load\_fixture("tests/fixtures/weather\_data.json")
        > > >
        > > > Use in test [#use-in-test]
        > > >
        > > > with mock\_dlt\_source(data=test\_data) as source:
        > > > ...     result = my\_asset\_function(source)

        > > > Load CSV fixture [#load-csv-fixture]
        > > >
        > > > test\_df = load\_fixture("tests/fixtures/sample\_data.csv")
        > > > validated = MySchema.validate(test\_df)
      </Callout>

      Status: Fully implemented

      <PySourceCode>
        ```python
        def load_fixture(
            path: Union[str, Path],
        ) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
            """Load test fixture from file.

            Supports JSON, CSV, and Parquet files. Automatically detects format
            from file extension.

            Args:
                path: Path to fixture file (.json, .csv, or .parquet).

            Returns:
                Loaded data as DataFrame, dict, or list of dicts depending on format.

            Raises:
                FileNotFoundError: If file doesn't exist.
                ValueError: If file format is not supported.

            Example:
                >>> # Load JSON fixture
                >>> test_data = load_fixture("tests/fixtures/weather_data.json")
                >>> # Use in test
                >>> with mock_dlt_source(data=test_data) as source:
                ...     result = my_asset_function(source)

                >>> # Load CSV fixture
                >>> test_df = load_fixture("tests/fixtures/sample_data.csv")
                >>> validated = MySchema.validate(test_df)

            Status: Fully implemented

            """
            path = Path(path)

            if not path.exists():
                raise FileNotFoundError(f"Fixture file not found: {path}")

            suffix = path.suffix.lower()

            if suffix == ".json":
                with open(path, "r") as f:
                    data = json.load(f)
                # If it's a list of dicts, return as-is for easy use with MockDLTSource
                # If it's a dict, return as-is
                return data

            elif suffix == ".csv":
                return pd.read_csv(path)

            elif suffix == ".parquet":
                return pd.read_parquet(path)

            else:
                raise ValueError(
                    f"Unsupported fixture format: {suffix}. Supported formats: .json, .csv, .parquet"
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Union[str, Path]&#x22;" value="undefined">
          Path to fixture file (.json, .csv, or .parquet).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Union&#x22;">
        Loaded data as DataFrame, dict, or list of dicts depending on format.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;save_fixture&#x22;" type="&#x22;(data, path, pretty=True) -> None&#x22;">
      Save test data as fixture file.

      Automatically determines format from file extension.
      Creates parent directories if they don't exist.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > Save test data for reuse [#save-test-data-for-reuse]
        > > >
        > > > test\_data = \[
        > > > ...     \{"id": "1", "value": 42},
        > > > ...     \{"id": "2", "value": 84},
        > > > ... ]
        > > > save\_fixture(test\_data, "tests/fixtures/sample\_data.json")

        > > > Save DataFrame [#save-dataframe]
        > > >
        > > > df = pd.DataFrame(test\_data)
        > > > save\_fixture(df, "tests/fixtures/sample\_data.csv")

        > > > Later, load it in tests [#later-load-it-in-tests]
        > > >
        > > > loaded = load\_fixture("tests/fixtures/sample\_data.json")
      </Callout>

      Status: Fully implemented

      <PySourceCode>
        ```python
        def save_fixture(
            data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
            path: Union[str, Path],
            pretty: bool = True,
        ) -> None:
            """Save test data as fixture file.

            Automatically determines format from file extension.
            Creates parent directories if they don't exist.

            Args:
                data: Data to save (DataFrame, dict, or list of dicts).
                path: Path to save fixture file (.json, .csv, or .parquet).
                pretty: If True, format JSON with indentation (default: True).

            Raises:
                ValueError: If file format is not supported.

            Example:
                >>> # Save test data for reuse
                >>> test_data = [
                ...     {"id": "1", "value": 42},
                ...     {"id": "2", "value": 84},
                ... ]
                >>> save_fixture(test_data, "tests/fixtures/sample_data.json")

                >>> # Save DataFrame
                >>> df = pd.DataFrame(test_data)
                >>> save_fixture(df, "tests/fixtures/sample_data.csv")

                >>> # Later, load it in tests
                >>> loaded = load_fixture("tests/fixtures/sample_data.json")

            Status: Fully implemented

            """
            path = Path(path)

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            suffix = path.suffix.lower()

            if suffix == ".json":
                with open(path, "w") as f:
                    if pretty:
                        json.dump(data, f, indent=2, default=str)
                    else:
                        json.dump(data, f, default=str)

            elif suffix == ".csv":
                if isinstance(data, pd.DataFrame):
                    data.to_csv(path, index=False)
                else:
                    # Convert to DataFrame first
                    df: pd.DataFrame = (
                        pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                    )
                    df.to_csv(path, index=False)

            elif suffix == ".parquet":
                if isinstance(data, pd.DataFrame):
                    data.to_parquet(path, index=False)
                else:
                    # Convert to DataFrame first
                    df: pd.DataFrame = (
                        pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
                    )
                    df.to_parquet(path, index=False)

            else:
                raise ValueError(
                    f"Unsupported fixture format: {suffix}. Supported formats: .json, .csv, .parquet"
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]&#x22;" value="undefined">
          Data to save (DataFrame, dict, or list of dicts).
        </PyParameter>

        <PyParameter name="&#x22;path&#x22;" type="&#x22;Union[str, Path]&#x22;" value="undefined">
          Path to save fixture file (.json, .csv, or .parquet).
        </PyParameter>

        <PyParameter name="&#x22;pretty&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          If True, format JSON with indentation (default: True).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
