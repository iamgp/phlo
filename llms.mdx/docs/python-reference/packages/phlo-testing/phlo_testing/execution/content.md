# execution (/docs/python-reference/packages/phlo-testing/phlo_testing/execution)



Helper to execute assets with mocked dependencies and capture results.

Provides `test_asset_execution()` for running `@phlo_ingestion` assets in tests
with mocked Iceberg, Trino, and DLT dependencies.

Example:

> > > result = test\_asset\_execution(
> > > ...     my\_asset,
> > > ...     partition="2024-01-01",
> > > ...     mock\_data=\[\{"id": 1, "name": "Alice"}],
> > > ... )
> > > assert result.success
> > > assert len(result.data) == 1

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;AssetTestResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/execution/AssetTestResult&#x22;" />

      <Card title="&#x22;MockAssetContext&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/execution/MockAssetContext&#x22;" />

      <Card title="&#x22;TestAssetExecutor&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/execution/TestAssetExecutor&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;test_asset_execution&#x22;" type="&#x22;(asset_fn, partition='2024-01-01', mock_data=None, mock_iceberg=None, mock_trino=None, expected_schema=None, materialize_kwargs=None, _pytest_skip=True) -> AssetTestResult&#x22;">
      Execute an asset with mocked dependencies.

      Runs a `@phlo_ingestion` asset in isolation with mocked Iceberg,
      Trino, and DLT services. Captures results and logs for inspection.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > @phlo\_ingestion(
        > > > ...     unique\_key="id",
        > > > ...     validation\_schema=MySchema,
        > > > ... )
        > > > ... def my\_asset(partition\_date: str):
        > > > ...     return \[\{"id": 1, "name": "Alice"}]
        > > > ...
        > > > result = test\_asset\_execution(
        > > > ...     my\_asset,
        > > > ...     partition="2024-01-01",
        > > > ... )
        > > > assert result.success
        > > > assert len(result.data) == 1
      </Callout>

      <PySourceCode>
        ```python
        def test_asset_execution(
            asset_fn: Callable,
            partition: str = "2024-01-01",
            mock_data: Optional[list[dict[str, Any]]] = None,
            mock_iceberg: Optional[MockIcebergCatalog] = None,
            mock_trino: Optional[MockTrinoResource] = None,
            expected_schema: Optional[Any] = None,
            materialize_kwargs: Optional[dict[str, Any]] = None,
            _pytest_skip: bool = True,  # Flag to prevent pytest collection
        ) -> AssetTestResult:
            """Execute an asset with mocked dependencies.

            Runs a `@phlo_ingestion` asset in isolation with mocked Iceberg,
            Trino, and DLT services. Captures results and logs for inspection.

            Args:
                asset_fn: Asset function to test.
                partition: Partition key (e.g., "2024-01-01").
                mock_data: Mock data to return from DLT source.
                mock_iceberg: Pre-configured MockIcebergCatalog (uses new if None).
                mock_trino: Pre-configured MockTrinoResource (uses new if None).
                expected_schema: Pandera schema to validate results.
                materialize_kwargs: Extra kwargs to pass to materialize.
                _pytest_skip: Flag to prevent pytest from collecting as test.

            Returns:
                AssetTestResult with execution details.

            Raises:
                ValueError: If asset execution fails (and success=False in result).

            Example:
                >>> @phlo_ingestion(
                ...     unique_key="id",
                ...     validation_schema=MySchema,
                ... )
                ... def my_asset(partition_date: str):
                ...     return [{"id": 1, "name": "Alice"}]
                ...
                >>> result = test_asset_execution(
                ...     my_asset,
                ...     partition="2024-01-01",
                ... )
                >>> assert result.success
                >>> assert len(result.data) == 1

            """
            if mock_data is None:
                mock_data = []

            if materialize_kwargs is None:
                materialize_kwargs = {}

            start_time = time.time()
            context = MockAssetContext(
                partition_key=partition,
                mock_iceberg=mock_iceberg,
                mock_trino=mock_trino,
            )

            try:
                # Call asset function with mock context
                result = asset_fn(partition_date=partition)

                # Convert result to DataFrame if needed
                if isinstance(result, pd.DataFrame):
                    data = result
                elif isinstance(result, list):
                    data = pd.DataFrame(result) if result else pd.DataFrame()
                else:
                    # Assume it's an iterator/generator
                    data = pd.DataFrame(list(result)) if result else pd.DataFrame()

                # Validate against expected schema if provided
                if expected_schema is not None:
                    try:
                        expected_schema.validate(data)
                    except Exception as e:
                        return AssetTestResult(
                            success=False,
                            data=data,
                            logs=context.logs,
                            duration=time.time() - start_time,
                            error=ValueError(f"Schema validation failed: {e}"),
                        )

                return AssetTestResult(
                    success=True,
                    data=data,
                    metadata={
                        "row_count": len(data),
                        "columns": list(data.columns),
                        "partition": partition,
                    },
                    logs=context.logs,
                    duration=time.time() - start_time,
                    raw_result=result,
                )

            except Exception as e:
                return AssetTestResult(
                    success=False,
                    logs=context.logs,
                    duration=time.time() - start_time,
                    error=e,
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable&#x22;" value="undefined">
          Asset function to test.
        </PyParameter>

        <PyParameter name="&#x22;partition&#x22;" type="&#x22;str&#x22;" value="&#x22;'2024-01-01'&#x22;">
          Partition key (e.g., "2024-01-01").
        </PyParameter>

        <PyParameter name="&#x22;mock_data&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;">
          Mock data to return from DLT source.
        </PyParameter>

        <PyParameter name="&#x22;mock_iceberg&#x22;" type="&#x22;Optional[MockIcebergCatalog]&#x22;" value="&#x22;None&#x22;">
          Pre-configured MockIcebergCatalog (uses new if None).
        </PyParameter>

        <PyParameter name="&#x22;mock_trino&#x22;" type="&#x22;Optional[MockTrinoResource]&#x22;" value="&#x22;None&#x22;">
          Pre-configured MockTrinoResource (uses new if None).
        </PyParameter>

        <PyParameter name="&#x22;expected_schema&#x22;" type="&#x22;Optional[Any]&#x22;" value="&#x22;None&#x22;">
          Pandera schema to validate results.
        </PyParameter>

        <PyParameter name="&#x22;materialize_kwargs&#x22;" type="&#x22;Optional[dict[str, Any]]&#x22;" value="&#x22;None&#x22;">
          Extra kwargs to pass to materialize.
        </PyParameter>

        <PyParameter name="&#x22;_pytest_skip&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Flag to prevent pytest from collecting as test.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.execution.AssetTestResult&#x22;">
        AssetTestResult with execution details.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;test_asset_with_catalog&#x22;" type="&#x22;(asset_fn, partition='2024-01-01', catalog=None) -> AssetTestResult&#x22;">
      Execute an asset with access to mock Iceberg catalog.

      Useful for testing assets that read from or write to Iceberg tables.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > catalog = MockIcebergCatalog()
        > > >
        > > > Set up tables in catalog [#set-up-tables-in-catalog]
        > > >
        > > > result = test\_asset\_with\_catalog(
        > > > ...     my\_transform\_asset,
        > > > ...     partition="2024-01-01",
        > > > ...     catalog=catalog,
        > > > ... )
      </Callout>

      <PySourceCode>
        ```python
        def test_asset_with_catalog(
            asset_fn: Callable,
            partition: str = "2024-01-01",
            catalog: Optional[MockIcebergCatalog] = None,
        ) -> AssetTestResult:
            """Execute an asset with access to mock Iceberg catalog.

            Useful for testing assets that read from or write to Iceberg tables.

            Args:
                asset_fn: Asset function to test.
                partition: Partition key.
                catalog: Pre-configured MockIcebergCatalog.

            Returns:
                AssetTestResult with catalog access.

            Example:
                >>> catalog = MockIcebergCatalog()
                >>> # Set up tables in catalog
                >>> result = test_asset_with_catalog(
                ...     my_transform_asset,
                ...     partition="2024-01-01",
                ...     catalog=catalog,
                ... )

            """
            if catalog is None:
                catalog = MockIcebergCatalog()

            return test_asset_execution(
                asset_fn,
                partition=partition,
                mock_iceberg=catalog,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable&#x22;" value="undefined">
          Asset function to test.
        </PyParameter>

        <PyParameter name="&#x22;partition&#x22;" type="&#x22;str&#x22;" value="&#x22;'2024-01-01'&#x22;">
          Partition key.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;Optional[MockIcebergCatalog]&#x22;" value="&#x22;None&#x22;">
          Pre-configured MockIcebergCatalog.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.execution.AssetTestResult&#x22;">
        AssetTestResult with catalog access.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;test_asset_with_trino&#x22;" type="&#x22;(asset_fn, partition='2024-01-01', trino=None) -> AssetTestResult&#x22;">
      Execute an asset with access to mock Trino resource.

      Useful for testing quality checks and transform assets.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > trino = MockTrinoResource()
        > > >
        > > > Set up tables in Trino [#set-up-tables-in-trino]
        > > >
        > > > result = test\_asset\_with\_trino(
        > > > ...     my\_quality\_check,
        > > > ...     trino=trino,
        > > > ... )
      </Callout>

      <PySourceCode>
        ```python
        def test_asset_with_trino(
            asset_fn: Callable,
            partition: str = "2024-01-01",
            trino: Optional[MockTrinoResource] = None,
        ) -> AssetTestResult:
            """Execute an asset with access to mock Trino resource.

            Useful for testing quality checks and transform assets.

            Args:
                asset_fn: Asset function to test.
                partition: Partition key.
                trino: Pre-configured MockTrinoResource.

            Returns:
                AssetTestResult with Trino access.

            Example:
                >>> trino = MockTrinoResource()
                >>> # Set up tables in Trino
                >>> result = test_asset_with_trino(
                ...     my_quality_check,
                ...     trino=trino,
                ... )

            """
            if trino is None:
                trino = MockTrinoResource()

            return test_asset_execution(
                asset_fn,
                partition=partition,
                mock_trino=trino,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable&#x22;" value="undefined">
          Asset function to test.
        </PyParameter>

        <PyParameter name="&#x22;partition&#x22;" type="&#x22;str&#x22;" value="&#x22;'2024-01-01'&#x22;">
          Partition key.
        </PyParameter>

        <PyParameter name="&#x22;trino&#x22;" type="&#x22;Optional[MockTrinoResource]&#x22;" value="&#x22;None&#x22;">
          Pre-configured MockTrinoResource.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.execution.AssetTestResult&#x22;">
        AssetTestResult with Trino access.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
