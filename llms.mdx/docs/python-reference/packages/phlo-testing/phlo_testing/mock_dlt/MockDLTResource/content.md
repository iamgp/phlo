# MockDLTResource (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt/MockDLTResource)



Mock DLT resource that yields predefined data.

Mimics the interface of a DLT resource but returns fixed data
instead of fetching from an API.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Name of the resource.
</PyAttribute>

<PyAttribute name="&#x22;data&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null">
  List of records to yield.
</PyAttribute>

<PyAttribute name="&#x22;_index&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;">
  Current iteration index (internal use).
</PyAttribute>

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Get resource metadata.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__iter__&#x22;" type="&#x22;(self) -> Iterator[dict[str, Any]]&#x22;">
  Iterate over resource data.

  <PySourceCode>
    ```python
    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over resource data.

        Yields:
            Dictionary representing each record.

        """
        self._index = 0
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterator[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__next__&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Get next record.

  <PySourceCode>
    ```python
    def __next__(self) -> dict[str, Any]:
        """Get next record.

        Returns:
            Next record dictionary.

        Raises:
            StopIteration: When all records have been yielded.

        """
        if self._index >= len(self.data):
            raise StopIteration
        record = self.data[self._index]
        self._index += 1
        return record
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Next record dictionary.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_infer_schema&#x22;" type="&#x22;(self) -> dict[str, str]&#x22;">
  Infer schema from data.

  <PySourceCode>
    ```python
    def _infer_schema(self) -> dict[str, str]:
        """Infer schema from data.

        Returns:
            Dictionary mapping column names to inferred types.

        """
        if not self.data:
            return {}

        first_record = self.data[0]
        schema = {}

        for key, value in first_record.items():
            if isinstance(value, int):
                schema[key] = "bigint"
            elif isinstance(value, float):
                schema[key] = "double"
            elif isinstance(value, bool):
                schema[key] = "boolean"
            elif isinstance(value, str):
                schema[key] = "text"
            elif isinstance(value, pd.Timestamp) or hasattr(value, "isoformat"):
                schema[key] = "timestamp"
            else:
                schema[key] = "text"

        return schema
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary mapping column names to inferred types.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, data, _index=0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;data&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="null" />

    <PyParameter name="&#x22;_index&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
