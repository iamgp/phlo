# MockDLTSource (/docs/python-reference/packages/phlo-testing/phlo_testing/placeholders/MockDLTSource)



Mock DLT source for testing ingestion assets without API calls.

Creates a DLT-compatible source from test data, allowing tests to validate
schema validation, data transformations, and asset logic without requiring
actual API connections.

Attributes [#attributes]

<PyAttribute name="&#x22;data&#x22;" type="null" value="&#x22;data.to_dict('records')&#x22;">
  List of dictionaries representing records.
</PyAttribute>

<PyAttribute name="&#x22;_dataframe&#x22;" type="null" value="&#x22;data&#x22;" />

<PyAttribute name="&#x22;resource_name&#x22;" type="null" value="&#x22;resource_name&#x22;">
  Name of the mock DLT resource.
</PyAttribute>

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Return the resource name.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, data, resource_name='mock_resource')&#x22;">
  Initialize mock DLT source.

  <PySourceCode>
    ```python
    def __init__(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        resource_name: str = "mock_resource",
    ):
        """Initialize mock DLT source.

        Args:
            data: Either list of dictionaries or pandas DataFrame containing
                test data records.
            resource_name: Name of the mock DLT resource for identification.

        Raises:
            TypeError: If data is neither list of dicts nor DataFrame.

        """
        if isinstance(data, pd.DataFrame):
            self.data = data.to_dict("records")
            self._dataframe = data
        else:
            self.data = data
            self._dataframe = None

        self.resource_name = resource_name
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Union[List[Dict[str, Any]], pd.DataFrame]&#x22;" value="undefined">
      Either list of dictionaries or pandas DataFrame containing
      test data records.
    </PyParameter>

    <PyParameter name="&#x22;resource_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'mock_resource'&#x22;">
      Name of the mock DLT resource for identification.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;__iter__&#x22;" type="&#x22;(self) -> Iterator[Dict[str, Any]]&#x22;">
  Iterate over mock data rows.

  <PySourceCode>
    ```python
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over mock data rows.

        Yields:
            Dictionary representing each data record.

        """
        for row in self.data:
            yield row
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterator[typing.Dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__call__&#x22;" type="&#x22;(self)&#x22;">
  Make the source callable like a DLT resource.

  <PySourceCode>
    ```python
    def __call__(self):
        """Make the source callable like a DLT resource.

        Returns:
            Self for DLT compatibility.

        """
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null">
    Self for DLT compatibility.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_pandas&#x22;" type="&#x22;(self) -> pd.DataFrame&#x22;">
  Convert mock data to pandas DataFrame.

  <PySourceCode>
    ```python
    def to_pandas(self) -> pd.DataFrame:
        """Convert mock data to pandas DataFrame.

        Returns:
            DataFrame containing all records.

        """
        if self._dataframe is not None:
            return self._dataframe
        return pd.DataFrame(self.data)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
    DataFrame containing all records.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__len__&#x22;" type="&#x22;(self) -> int&#x22;">
  Return number of rows.

  <PySourceCode>
    ```python
    def __len__(self) -> int:
        """Return number of rows.

        Returns:
            Integer count of records.

        """
        return len(self.data)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;">
    Integer count of records.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__repr__&#x22;" type="&#x22;(self) -> str&#x22;">
  String representation.

  <PySourceCode>
    ```python
    def __repr__(self) -> str:
        """String representation.

        Returns:
            String with resource name and row count.

        """
        return f"MockDLTSource(resource_name='{self.resource_name}', rows={len(self.data)})"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    String with resource name and row count.
  </PyFunctionReturn>
</PyFunction>
