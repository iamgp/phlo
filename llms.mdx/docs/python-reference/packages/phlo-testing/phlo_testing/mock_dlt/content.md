# mock_dlt (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt)



Mock DLT sources for testing without API calls.

Provides mock implementations of DLT sources that return predefined data,
enabling tests to run without external dependencies or network calls.

Example:

> > > data = \[\{"id": 1, "name": "Alice"}, \{"id": 2, "name": "Bob"}]
> > > source = mock\_dlt\_source(data, resource\_name="users")
> > > for record in source:
> > > ...     print(record)

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MockDLTResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt/MockDLTResource&#x22;" />

      <Card title="&#x22;MockDLTSource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt/MockDLTSource&#x22;" />

      <Card title="&#x22;MockDLTError&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt/MockDLTError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;mock_dlt_source&#x22;" type="&#x22;(data, resource_name='default') -> MockDLTResource&#x22;">
      Create a mock DLT source with a single resource.

      Drop-in replacement for `dlt.resource()` that returns predefined data
      without making API calls.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > data = \[\{"id": 1, "name": "Alice"}, \{"id": 2, "name": "Bob"}]
        > > > source = mock\_dlt\_source(data, resource\_name="users")
        > > > for record in source:
        > > > ...     print(record)
        > > > \{"id": 1, "name": "Alice"}
        > > > \{"id": 2, "name": "Bob"}
      </Callout>

      <PySourceCode>
        ```python
        def mock_dlt_source(
            data: list[dict[str, Any]],
            resource_name: str = "default",
        ) -> MockDLTResource:
            """Create a mock DLT source with a single resource.

            Drop-in replacement for `dlt.resource()` that returns predefined data
            without making API calls.

            Args:
                data: List of records to return.
                resource_name: Name of the resource.

            Returns:
                MockDLTResource instance.

            Example:
                >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
                >>> source = mock_dlt_source(data, resource_name="users")
                >>> for record in source:
                ...     print(record)
                {"id": 1, "name": "Alice"}
                {"id": 2, "name": "Bob"}

            """
            return MockDLTResource(name=resource_name, data=data)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
          List of records to return.
        </PyParameter>

        <PyParameter name="&#x22;resource_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'default'&#x22;">
          Name of the resource.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;">
        MockDLTResource instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;mock_dlt_source_multi&#x22;" type="&#x22;(resources) -> MockDLTSource&#x22;">
      Create a mock DLT source with multiple resources.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > source = mock\_dlt\_source\_multi(\{
        > > > ...     "users": \[\{"id": 1, "name": "Alice"}],
        > > > ...     "orders": \[\{"order\_id": 1, "user\_id": 1}],
        > > > ... })
        > > > for record in source:
        > > > ...     print(record)
      </Callout>

      <PySourceCode>
        ```python
        def mock_dlt_source_multi(
            resources: dict[str, list[dict[str, Any]]],
        ) -> MockDLTSource:
            """Create a mock DLT source with multiple resources.

            Args:
                resources: Dict mapping resource names to data lists.

            Returns:
                MockDLTSource instance.

            Example:
                >>> source = mock_dlt_source_multi({
                ...     "users": [{"id": 1, "name": "Alice"}],
                ...     "orders": [{"order_id": 1, "user_id": 1}],
                ... })
                >>> for record in source:
                ...     print(record)

            """
            mock_source = MockDLTSource()
            for name, data in resources.items():
                mock_source.add_resource(name, data)
            return mock_source
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;resources&#x22;" type="&#x22;dict[str, list[dict[str, Any]]]&#x22;" value="undefined">
          Dict mapping resource names to data lists.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTSource&#x22;">
        MockDLTSource instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;mock_dlt_source_with_error&#x22;" type="&#x22;(data, resource_name='default', error_after=None, error_message='Mock DLT error') -> MockDLTResource&#x22;">
      Create a mock DLT source that raises an error after N records.

      Useful for testing error handling in ingestion pipelines.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > source = mock\_dlt\_source\_with\_error(
        > > > ...     \[\{"id": 1}, \{"id": 2}],
        > > > ...     error\_after=1,
        > > > ...     error\_message="API rate limit exceeded"
        > > > ... )
        > > > records = list(source)  # Raises after 1 record
      </Callout>

      <PySourceCode>
        ```python
        def mock_dlt_source_with_error(
            data: list[dict[str, Any]],
            resource_name: str = "default",
            error_after: int | None = None,
            error_message: str = "Mock DLT error",
        ) -> MockDLTResource:
            """Create a mock DLT source that raises an error after N records.

            Useful for testing error handling in ingestion pipelines.

            Args:
                data: List of records to return before error.
                resource_name: Name of the resource.
                error_after: Number of records before error (None = no error).
                error_message: Error message to raise.

            Returns:
                MockDLTResource instance that raises error at specified point.

            Example:
                >>> source = mock_dlt_source_with_error(
                ...     [{"id": 1}, {"id": 2}],
                ...     error_after=1,
                ...     error_message="API rate limit exceeded"
                ... )
                >>> records = list(source)  # Raises after 1 record

            """

            class ErrorRaisingResource(MockDLTResource):
                """Resource that raises an error after N records."""

                def __next__(self) -> dict[str, Any]:
                    """Return the next record or raise a configured mock error.

                    Returns:
                        The next record from the underlying mock resource.

                    Raises:
                        MockDLTError: If the configured error threshold is reached.

                    """
                    if error_after is not None and self._index >= error_after:
                        raise MockDLTError(error_message)
                    return super().__next__()

            return ErrorRaisingResource(name=resource_name, data=data)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
          List of records to return before error.
        </PyParameter>

        <PyParameter name="&#x22;resource_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'default'&#x22;">
          Name of the resource.
        </PyParameter>

        <PyParameter name="&#x22;error_after&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
          Number of records before error (None = no error).
        </PyParameter>

        <PyParameter name="&#x22;error_message&#x22;" type="&#x22;str&#x22;" value="&#x22;'Mock DLT error'&#x22;">
          Error message to raise.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;">
        MockDLTResource instance that raises error at specified point.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;mock_dlt_pipeline&#x22;" type="&#x22;(data) -> MockDLTSource&#x22;">
      Create a mock DLT pipeline with multiple resources.

      Convenience function for creating a complete mock pipeline.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > pipeline = mock\_dlt\_pipeline(\{
        > > > ...     "users": \[\{"id": 1, "name": "Alice"}],
        > > > ...     "orders": \[\{"order\_id": 1, "user\_id": 1}],
        > > > ... })
      </Callout>

      <PySourceCode>
        ```python
        def mock_dlt_pipeline(
            data: dict[str, list[dict[str, Any]]],
        ) -> MockDLTSource:
            """Create a mock DLT pipeline with multiple resources.

            Convenience function for creating a complete mock pipeline.

            Args:
                data: Dict mapping table names to records.

            Returns:
                MockDLTSource instance.

            Example:
                >>> pipeline = mock_dlt_pipeline({
                ...     "users": [{"id": 1, "name": "Alice"}],
                ...     "orders": [{"order_id": 1, "user_id": 1}],
                ... })

            """
            return mock_dlt_source_multi(data)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data&#x22;" type="&#x22;dict[str, list[dict[str, Any]]]&#x22;" value="undefined">
          Dict mapping table names to records.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTSource&#x22;">
        MockDLTSource instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;create_mock_dlt_dataframe&#x22;" type="&#x22;(resource) -> pd.DataFrame&#x22;">
      Convert mock DLT resource to pandas DataFrame.

      Helper for testing data transformations.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > source = mock\_dlt\_source(\[\{"id": 1}, \{"id": 2}])
        > > > df = create\_mock\_dlt\_dataframe(source)
      </Callout>

      <PySourceCode>
        ```python
        def create_mock_dlt_dataframe(
            resource: MockDLTResource,
        ) -> pd.DataFrame:
            """Convert mock DLT resource to pandas DataFrame.

            Helper for testing data transformations.

            Args:
                resource: MockDLTResource instance.

            Returns:
                DataFrame with resource data.

            Example:
                >>> source = mock_dlt_source([{"id": 1}, {"id": 2}])
                >>> df = create_mock_dlt_dataframe(source)

            """
            return pd.DataFrame(list(resource))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;resource&#x22;" type="&#x22;MockDLTResource&#x22;" value="undefined">
          MockDLTResource instance.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
        DataFrame with resource data.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
