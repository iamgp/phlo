# ApiBackend (/docs/python-reference/core/phlo/capabilities/interfaces/ApiBackend)



Protocol for swappable API and graph-serving backends.

Functions [#functions]

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check backend connectivity and readiness.

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check backend connectivity and readiness."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;describe&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return backend metadata and public endpoint information.

  <PySourceCode>
    ```python
    def describe(self) -> dict[str, Any]:
        """Return backend metadata and public endpoint information."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
</PyFunction>
