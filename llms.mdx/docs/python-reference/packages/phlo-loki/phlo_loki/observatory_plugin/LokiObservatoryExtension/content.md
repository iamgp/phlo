# LokiObservatoryExtension (/docs/python-reference/packages/phlo-loki/phlo_loki/observatory_plugin/LokiObservatoryExtension)



Observatory extension for Loki log aggregation UI.

This extension integrates Loki log viewing capabilities into the Phlo
Observatory web interface. It provides navigation to the logs view and
serves bundled static assets for the log UI components.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin identity metadata for discovery.
</PyAttribute>

<PyAttribute name="&#x22;manifest&#x22;" type="&#x22;ObservatoryExtensionManifest&#x22;" value="null">
  Return extension manifest for Observatory navigation and compatibility.
</PyAttribute>

<PyAttribute name="&#x22;asset_root&#x22;" type="&#x22;Traversable&#x22;" value="null">
  Return package path to static observatory extension assets.
</PyAttribute>
