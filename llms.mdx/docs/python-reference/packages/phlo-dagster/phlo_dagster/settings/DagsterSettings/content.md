# DagsterSettings (/docs/python-reference/packages/phlo-dagster/phlo_dagster/settings/DagsterSettings)



Dagster orchestration configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;dagster_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10006, description='Dagster webserver port')&#x22;" />

<PyAttribute name="&#x22;workflows_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='workflows', description='Path to user workflows directory (for external projects)')&#x22;" />

<PyAttribute name="&#x22;phlo_force_in_process_executor&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=False, description='Force use of in-process executor')&#x22;" />

<PyAttribute name="&#x22;phlo_force_multiprocess_executor&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=False, description='Force use of multiprocess executor')&#x22;" />

<PyAttribute name="&#x22;phlo_host_platform&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Host platform for executor selection (Darwin/Linux/Windows). Auto-detected in CLI; set explicitly for daemon/webserver on macOS.')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;validate_executor_flags&#x22;" type="&#x22;(self) -> 'DagsterSettings'&#x22;">
  Validate mutually exclusive executor override flags.

  <PySourceCode>
    ```python
    @model_validator(mode="after")
    def validate_executor_flags(self) -> "DagsterSettings":
        """Validate mutually exclusive executor override flags.

        Args:
            None (operates on self).

        Returns:
            Validated settings instance.

        Raises:
            ValueError: If both force flags are set simultaneously.

        """
        if self.phlo_force_in_process_executor and self.phlo_force_multiprocess_executor:
            raise ValueError(
                "phlo_force_in_process_executor and phlo_force_multiprocess_executor "
                "cannot both be True"
            )
        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'DagsterSettings'&#x22;">
    Validated settings instance.
  </PyFunctionReturn>
</PyFunction>
