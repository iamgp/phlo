# ServiceOverride (/docs/python-reference/core/phlo/config_schema/ServiceOverride)



User overrides for a service in phlo.yaml.

Allows customizing installed service configurations without
modifying the package's bundled service.yaml.

Example in phlo.yaml:
services:
observatory:
enabled: true
ports:

* "8080:3000"
  environment:
  DEBUG: "true"
  superset:
  enabled: false

Attributes [#attributes]

<PyAttribute name="&#x22;enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Whether to include this service. Set to false to disable.')&#x22;" />

<PyAttribute name="&#x22;ports&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;Field(default=None, description='Port mappings to override (replaces package defaults).')&#x22;" />

<PyAttribute name="&#x22;environment&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;Field(default=None, description='Environment variables to add/override (merged with package defaults).')&#x22;" />

<PyAttribute name="&#x22;volumes&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;Field(default=None, description='Volume mounts to add (appended to package defaults).')&#x22;" />

<PyAttribute name="&#x22;depends_on&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;Field(default=None, description='Service dependencies to override (replaces package defaults).')&#x22;" />

<PyAttribute name="&#x22;command&#x22;" type="&#x22;str | list[str] | None&#x22;" value="&#x22;Field(default=None, description='Container command override.')&#x22;" />

<PyAttribute name="&#x22;type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description=\&#x22;Service type. Set to 'inline' for custom services defined in phlo.yaml.\&#x22;)&#x22;" />

<PyAttribute name="&#x22;image&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Docker image for inline services.')&#x22;" />

<PyAttribute name="&#x22;build&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;Field(default=None, description='Build configuration for inline services.')&#x22;" />

<PyAttribute name="&#x22;healthcheck&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;Field(default=None, description='Healthcheck configuration for inline services.')&#x22;" />
