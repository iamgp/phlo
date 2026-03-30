# MaintenanceReadModel (/docs/python-reference/core/phlo/capabilities/interfaces/MaintenanceReadModel)



Protocol for maintenance and observability status read models.

Functions [#functions]

<PyFunction name="&#x22;load_maintenance_status&#x22;" type="&#x22;(self) -> Any&#x22;">
  Load the current maintenance status snapshot.

  <PySourceCode>
    ```python
    def load_maintenance_status(self) -> Any:
        """Load the current maintenance status snapshot."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
</PyFunction>

<PyFunction name="&#x22;render_maintenance_prometheus&#x22;" type="&#x22;(self) -> str&#x22;">
  Render maintenance metrics in Prometheus text format.

  <PySourceCode>
    ```python
    def render_maintenance_prometheus(self) -> str:
        """Render maintenance metrics in Prometheus text format."""
        ...
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>
