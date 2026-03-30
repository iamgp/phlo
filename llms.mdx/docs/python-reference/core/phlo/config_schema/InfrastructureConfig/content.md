# InfrastructureConfig (/docs/python-reference/core/phlo/config_schema/InfrastructureConfig)



Infrastructure configuration section from phlo.yaml.

Attributes [#attributes]

<PyAttribute name="&#x22;container_naming_pattern&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='{project}-{service}-1', description='Pattern for generating container names. Available variables: {project}, {service}')&#x22;" />

<PyAttribute name="&#x22;services&#x22;" type="&#x22;dict[str, ServiceConfig]&#x22;" value="&#x22;Field(default_factory=dict, description='Service definitions keyed by service identifier')&#x22;" />

<PyAttribute name="&#x22;network&#x22;" type="&#x22;NetworkConfig&#x22;" value="&#x22;Field(default_factory=NetworkConfig, description='Docker network configuration')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;validate_pattern&#x22;" type="&#x22;(cls, v) -> str&#x22;">
  Validate a container naming pattern.

  <PySourceCode>
    ```python
    @field_validator("container_naming_pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate a container naming pattern.

        Args:
            v: Naming pattern template.

        Returns:
            str: Original pattern when valid.

        Raises:
            ValueError: If pattern includes neither `{project}` nor `{service}`.
        """
        if "{project}" not in v and "{service}" not in v:
            raise ValueError(
                "container_naming_pattern must contain at least {project} or {service}"
            )
        return v
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;v&#x22;" type="&#x22;str&#x22;" value="undefined">
      Naming pattern template.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Original pattern when valid.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_service&#x22;" type="&#x22;(self, service_key) -> ServiceConfig | None&#x22;">
  Get service configuration by key.

  <PySourceCode>
    ```python
    def get_service(self, service_key: str) -> ServiceConfig | None:
        """Get service configuration by key."""
        return self.services.get(service_key)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_key&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.config_schema.ServiceConfig | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_container_name&#x22;" type="&#x22;(self, service_key, project_name) -> str | None&#x22;">
  Get container name for a service.

  <PySourceCode>
    ```python
    def get_container_name(self, service_key: str, project_name: str) -> str | None:
        """Get container name for a service."""
        service = self.get_service(service_key)
        if not service:
            return None
        return service.get_container_name(project_name, self.container_naming_pattern)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_key&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;" />
</PyFunction>
