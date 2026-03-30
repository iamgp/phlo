# PanderaObservatoryExtension (/docs/python-reference/packages/phlo-pandera/phlo_pandera/observatory_plugin/PanderaObservatoryExtension)



Observatory extension metadata for Quality UI pages.

This class provides the metadata and asset configuration needed to integrate
the Phlo Quality Framework with the Observatory web UI. It exposes a "Quality"
navigation item and references the static assets for quality dashboards.

The extension is automatically discovered by the Observatory plugin system
through the `phlo.observatory.extensions` entry point.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin metadata (name, version, description).
</PyAttribute>

<PyAttribute name="&#x22;manifest&#x22;" type="&#x22;ObservatoryExtensionManifest&#x22;" value="null">
  Extension manifest defining UI navigation and compatibility.
</PyAttribute>

<PyAttribute name="&#x22;asset_root&#x22;" type="&#x22;Traversable&#x22;" value="null">
  Path to packaged static assets.
</PyAttribute>
