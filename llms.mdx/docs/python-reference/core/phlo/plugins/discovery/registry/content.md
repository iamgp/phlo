# registry (/docs/python-reference/core/phlo/plugins/discovery/registry)



Plugin registry for managing loaded plugins.

The registry maintains a catalog of discovered plugins and provides
methods for accessing them by name and type.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PluginRegistry&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/registry/PluginRegistry&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_global_registry&#x22;" type="&#x22;() -> PluginRegistry&#x22;">
      Get the global plugin registry instance.

      <PySourceCode>
        ```python
        def get_global_registry() -> PluginRegistry:
            """
            Get the global plugin registry instance.

            Returns:
                Global PluginRegistry instance
            """
            return _global_registry
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry&#x22;">
        Global PluginRegistry instance
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
