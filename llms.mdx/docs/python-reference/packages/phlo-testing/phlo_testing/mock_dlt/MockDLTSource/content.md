# MockDLTSource (/docs/python-reference/packages/phlo-testing/phlo_testing/mock_dlt/MockDLTSource)



Mock DLT source with multiple resources.

Mimics the interface of a DLT source but returns fixed data
instead of fetching from an API. Supports multiple resources.

Attributes [#attributes]

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;dict[str, list[dict[str, Any]]]&#x22;" value="&#x22;field(default_factory=dict)&#x22;">
  Dictionary mapping resource names to data lists.
</PyAttribute>

<PyAttribute name="&#x22;_current_resource&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Currently selected resource (internal use).
</PyAttribute>

<PyAttribute name="&#x22;_current_index&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;">
  Current iteration index (internal use).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;add_resource&#x22;" type="&#x22;(self, name, data) -> MockDLTResource&#x22;">
  Add a resource to the source.

  <PySourceCode>
    ```python
    def add_resource(self, name: str, data: list[dict[str, Any]]) -> MockDLTResource:
        """Add a resource to the source.

        Args:
            name: Resource name.
            data: List of records.

        Returns:
            MockDLTResource instance.

        """
        self.resources[name] = data
        return MockDLTResource(name=name, data=data)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Resource name.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of records.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;">
    MockDLTResource instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_resource&#x22;" type="&#x22;(self, name) -> MockDLTResource&#x22;">
  Get a resource by name.

  <PySourceCode>
    ```python
    def get_resource(self, name: str) -> MockDLTResource:
        """Get a resource by name.

        Args:
            name: Resource name.

        Returns:
            MockDLTResource instance.

        Raises:
            ValueError: If resource doesn't exist.

        """
        if name not in self.resources:
            raise ValueError(f"Resource {name} not found")

        return MockDLTResource(name=name, data=self.resources[name])
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Resource name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;">
    MockDLTResource instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__iter__&#x22;" type="&#x22;(self) -> Iterator[dict[str, Any]]&#x22;">
  Iterate over all resources.

  <PySourceCode>
    ```python
    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over all resources.

        Yields:
            Dictionary representing each record from all resources.

        """
        for resource_name, data in self.resources.items():
            for record in data:
                yield record
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Iterator[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;for_each&#x22;" type="&#x22;(self, func) -> None&#x22;">
  Apply a function to each record.

  <PySourceCode>
    ```python
    def for_each(self, func: Any) -> None:
        """Apply a function to each record.

        Args:
            func: Function to apply (for dlt compatibility).

        """
        for record in self:
            func(record)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;func&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Function to apply (for dlt compatibility).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, resources=dict(), _current_resource=None, _current_index=0) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;dict[str, list[dict[str, Any]]]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;_current_resource&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;_current_index&#x22;" type="&#x22;int&#x22;" value="&#x22;0&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
