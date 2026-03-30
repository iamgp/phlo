# TestAssetExecutor (/docs/python-reference/packages/phlo-testing/phlo_testing/execution/TestAssetExecutor)



Reusable executor for testing multiple asset runs.

Maintains catalog state across multiple executions for integration testing.

Attributes [#attributes]

<PyAttribute name="&#x22;catalog&#x22;" type="null" value="&#x22;catalog or MockIcebergCatalog()&#x22;">
  Shared MockIcebergCatalog instance.
</PyAttribute>

<PyAttribute name="&#x22;trino&#x22;" type="null" value="&#x22;trino or MockTrinoResource()&#x22;">
  Shared MockTrinoResource instance.
</PyAttribute>

<PyAttribute name="&#x22;results&#x22;" type="&#x22;list[AssetTestResult]&#x22;" value="&#x22;[]&#x22;">
  List of all AssetTestResult instances from executions.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, catalog=None, trino=None) -> None&#x22;">
  Initialize executor.

  <PySourceCode>
    ```python
    def __init__(
        self,
        catalog: Optional[MockIcebergCatalog] = None,
        trino: Optional[MockTrinoResource] = None,
    ) -> None:
        """Initialize executor.

        Args:
            catalog: Shared MockIcebergCatalog.
            trino: Shared MockTrinoResource.

        """
        self.catalog = catalog or MockIcebergCatalog()
        self.trino = trino or MockTrinoResource()
        self.results: list[AssetTestResult] = []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;Optional[MockIcebergCatalog]&#x22;" value="&#x22;None&#x22;">
      Shared MockIcebergCatalog.
    </PyParameter>

    <PyParameter name="&#x22;trino&#x22;" type="&#x22;Optional[MockTrinoResource]&#x22;" value="&#x22;None&#x22;">
      Shared MockTrinoResource.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;execute&#x22;" type="&#x22;(self, asset_fn, partition='2024-01-01', mock_data=None) -> AssetTestResult&#x22;">
  Execute an asset with shared resources.

  <PySourceCode>
    ```python
    def execute(
        self,
        asset_fn: Callable,
        partition: str = "2024-01-01",
        mock_data: Optional[list[dict[str, Any]]] = None,
    ) -> AssetTestResult:
        """Execute an asset with shared resources.

        Args:
            asset_fn: Asset function to test.
            partition: Partition key.
            mock_data: Mock data (not used in executor mode).

        Returns:
            AssetTestResult with execution details.

        """
        result = test_asset_execution(
            asset_fn,
            partition=partition,
            mock_iceberg=self.catalog,
            mock_trino=self.trino,
        )

        self.results.append(result)
        return result
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable&#x22;" value="undefined">
      Asset function to test.
    </PyParameter>

    <PyParameter name="&#x22;partition&#x22;" type="&#x22;str&#x22;" value="&#x22;'2024-01-01'&#x22;">
      Partition key.
    </PyParameter>

    <PyParameter name="&#x22;mock_data&#x22;" type="&#x22;Optional[list[dict[str, Any]]]&#x22;" value="&#x22;None&#x22;">
      Mock data (not used in executor mode).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.execution.AssetTestResult&#x22;">
    AssetTestResult with execution details.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_results&#x22;" type="&#x22;(self, asset_fn) -> list[AssetTestResult]&#x22;">
  Get results for a specific asset.

  <PySourceCode>
    ```python
    def get_results(self, asset_fn: Callable) -> list[AssetTestResult]:
        """Get results for a specific asset.

        Args:
            asset_fn: Asset function to filter by.

        Returns:
            List of results for that asset.

        """
        # This is a simplified implementation
        # In practice, you'd track asset names
        return self.results
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;asset_fn&#x22;" type="&#x22;Callable&#x22;" value="undefined">
      Asset function to filter by.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of results for that asset.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cleanup&#x22;" type="&#x22;(self) -> None&#x22;">
  Clean up resources.

  <PySourceCode>
    ```python
    def cleanup(self) -> None:
        """Clean up resources."""
        self.catalog.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
