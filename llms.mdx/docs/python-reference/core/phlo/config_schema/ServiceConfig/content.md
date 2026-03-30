# ServiceConfig (/docs/python-reference/core/phlo/config_schema/ServiceConfig)



Configuration for a single service.

Attributes [#attributes]

<PyAttribute name="&#x22;container_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Explicit container name override. If None, uses container_naming_pattern.')&#x22;" />

<PyAttribute name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(description=\&#x22;Docker compose service name (e.g., 'dagster-webserver', 'postgres')\&#x22;)&#x22;" />

<PyAttribute name="&#x22;host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default='localhost', description='External hostname for accessing the service')&#x22;" />

<PyAttribute name="&#x22;internal_host&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Internal Docker network hostname. If None, uses service_name.')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;validate_container_name&#x22;" type="&#x22;(cls, v) -> str | None&#x22;">
  Validate `container_name` characters and format.

  <PySourceCode>
    ```python
    @field_validator("container_name")
    @classmethod
    def validate_container_name(cls, v: str | None) -> str | None:
        """Validate `container_name` characters and format.

        Args:
            v: Candidate container name.

        Returns:
            Optional[str]: Original value when valid.

        Raises:
            ValueError: If the container name is empty or contains invalid characters.
        """
        if v is None:
            return v

        if not v:
            raise ValueError("container_name cannot be empty string")

        valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
        if not all(c in valid_chars for c in v.lower()):
            raise ValueError(
                "container_name must contain only alphanumeric characters, hyphens, underscores, and dots"
            )

        if v.startswith(("-", ".")):
            raise ValueError("container_name cannot start with hyphen or dot")

        return v
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;v&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Candidate container name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str | None&#x22;">
    Optional\[str]: Original value when valid.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;validate_service_name&#x22;" type="&#x22;(cls, v) -> str&#x22;">
  Validate and normalize a service name.

  <PySourceCode>
    ```python
    @field_validator("service_name")
    @classmethod
    def validate_service_name(cls, v: str) -> str:
        """Validate and normalize a service name.

        Args:
            v: Candidate service name.

        Returns:
            str: Trimmed service name.

        Raises:
            ValueError: If the service name is empty.
        """
        if not v or not v.strip():
            raise ValueError("service_name cannot be empty")
        return v.strip()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;v&#x22;" type="&#x22;str&#x22;" value="undefined">
      Candidate service name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Trimmed service name.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_container_name&#x22;" type="&#x22;(self, project_name, pattern) -> str&#x22;">
  Get effective container name, applying pattern if needed.

  <PySourceCode>
    ```python
    def get_container_name(self, project_name: str, pattern: str) -> str:
        """Get effective container name, applying pattern if needed."""
        if self.container_name:
            return self.container_name
        return pattern.format(project=project_name, service=self.service_name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;pattern&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_internal_host&#x22;" type="&#x22;(self) -> str&#x22;">
  Get effective internal hostname.

  <PySourceCode>
    ```python
    def get_internal_host(self) -> str:
        """Get effective internal hostname."""
        return self.internal_host or self.service_name
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>
