# discovery (/docs/python-reference/core/phlo/plugins/discovery)



Plugin Discovery Module

Consolidates plugin and service discovery into a single module under phlo.plugins.

This module provides a unified interface for discovering:

* Plugins (via entry points)
* Services (from plugins and core)
* Local in-memory registry access

Remote registry package discovery lives in phlo.plugins.registry\_client
(e.g., list\_registry\_plugins) and is not re-exported here.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['ENTRY_POINT_GROUPS', 'discover_plugins', 'get_plugin', 'get_plugin_info', 'get_quality_check', 'get_quality_provider', 'get_ingestion_provider', 'get_transformation_provider', 'get_service', 'get_hook_plugin', 'get_source_connector', 'get_transformation', 'list_plugins', 'validate_plugins', 'PluginRegistry', 'get_global_registry', 'ServiceDefinition', 'ServiceDiscovery']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_service_dependency_resolution&#x22;" title="&#x22;_service_dependency_resolution&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_registry_metadata&#x22;" title="&#x22;_registry_metadata&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_plugin_loading&#x22;" title="&#x22;_plugin_loading&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/services&#x22;" title="&#x22;services&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_registry_validation&#x22;" title="&#x22;_registry_validation&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_service_definition&#x22;" title="&#x22;_service_definition&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_service_loading&#x22;" title="&#x22;_service_loading&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_service_discovery&#x22;" title="&#x22;_service_discovery&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_plugin_lifecycle&#x22;" title="&#x22;_plugin_lifecycle&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/plugins&#x22;" title="&#x22;plugins&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_plugin_queries&#x22;" title="&#x22;_plugin_queries&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_registry_constants&#x22;" title="&#x22;_registry_constants&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_plugin_auto_discovery&#x22;" title="&#x22;_plugin_auto_discovery&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/registry&#x22;" title="&#x22;registry&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_plugin_constants&#x22;" title="&#x22;_plugin_constants&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins/discovery/_service_cycles&#x22;" title="&#x22;_service_cycles&#x22;" />
    </Cards>
  </Tab>
</Tabs>
