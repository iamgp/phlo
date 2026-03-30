# PluginMetadata (/docs/python-reference/core/phlo/plugins/base/plugin/PluginMetadata)



Metadata about a plugin.

This dataclass captures all essential information about a plugin including
identity, authorship, dependencies, and capability requirements. It is used
during plugin discovery, registration, and display.

Attributes [#attributes]

<PyAttribute name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null">
  Unique plugin name within its plugin type. Must be a valid
  Python identifier without spaces.
</PyAttribute>

<PyAttribute name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="null">
  Plugin version following semantic versioning (e.g., "1.0.0").
</PyAttribute>

<PyAttribute name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;">
  Human-readable description of what the plugin does.
</PyAttribute>

<PyAttribute name="&#x22;author&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;">
  Plugin author name, organization, or email.
</PyAttribute>

<PyAttribute name="&#x22;license&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;">
  SPDX license identifier (e.g., "MIT", "Apache-2.0", "GPL-3.0").
</PyAttribute>

<PyAttribute name="&#x22;homepage&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;">
  URL to the plugin repository or documentation.
</PyAttribute>

<PyAttribute name="&#x22;tags&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Categorization tags for plugin discovery (e.g., \["source", "api"]).
</PyAttribute>

<PyAttribute name="&#x22;dependencies&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Required Python packages with version constraints.
</PyAttribute>

<PyAttribute name="&#x22;requires_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Capability names that must be available for
  this plugin to function. Plugin loading will fail if unavailable.
</PyAttribute>

<PyAttribute name="&#x22;optional_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;field(default_factory=list)&#x22;">
  Capability names that enhance functionality
  when available, but are not required.
</PyAttribute>

<PyAttribute name="&#x22;support&#x22;" type="&#x22;CapabilitySupport&#x22;" value="&#x22;field(default_factory=CapabilitySupport)&#x22;">
  :class:`~phlo.capabilities.support.CapabilitySupport` declaring
  operational guarantees (best\_effort, self\_healing, etc.).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, name, version, description='', author='', license='', homepage='', tags=list(), dependencies=list(), requires_capabilities=list(), optional_capabilities=list(), support=CapabilitySupport()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;version&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;description&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;" />

    <PyParameter name="&#x22;author&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;" />

    <PyParameter name="&#x22;license&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;" />

    <PyParameter name="&#x22;homepage&#x22;" type="&#x22;str&#x22;" value="&#x22;''&#x22;" />

    <PyParameter name="&#x22;tags&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;dependencies&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;requires_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;optional_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;list()&#x22;" />

    <PyParameter name="&#x22;support&#x22;" type="&#x22;CapabilitySupport&#x22;" value="&#x22;CapabilitySupport()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
