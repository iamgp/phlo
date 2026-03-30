# ExampleObservatoryExtension (/docs/python-reference/packages/phlo-observatory-example/phlo_observatory_example/observatory_plugin/ExampleObservatoryExtension)



Example Observatory extension demonstrating plugin capabilities.

This extension provides a complete example of how to extend the
Phlo Observatory UI with custom routes, dashboard integrations,
and user-configurable settings.

The extension registers:

* A dedicated route at `/extensions/example`
* Navigation link in the sidebar
* Dashboard widget slots (after cards and hub stats)
* Settings panel with toggle and message configuration

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for extension discovery and registration.

  The metadata provides the extension's identity including name,
  version, and description. This information is used by the
  plugin system for dependency resolution and display purposes.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Access metadata for debugging or display::

    ext = ExampleObservatoryExtension()
    print(ext.metadata.name)  # "example"
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;manifest&#x22;" type="&#x22;ObservatoryExtensionManifest&#x22;" value="null">
  Return Observatory extension manifest with full configuration.

  The manifest defines all UI integrations, settings schemas, and
  compatibility requirements. It controls how the extension appears
  and behaves within the Observatory interface.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Inspect manifest configuration::

    ext = ExampleObservatoryExtension()
    manifest = ext.manifest
    print(manifest.ui.routes)  # List of routes
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    ObservatoryExtensionSettings: Configuration schema definition.
    ObservatoryExtensionUI: UI component registrations.
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;asset_root&#x22;" type="&#x22;Traversable&#x22;" value="null">
  Return the static asset directory for the extension.

  Assets in this directory (JavaScript bundles, images, etc.) are
  served by the Observatory server and made available to the
  extension's frontend components.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Access bundled JavaScript file::

    ext = ExampleObservatoryExtension()
    js\_path = ext.asset\_root.joinpath("example.js")
    content = js\_path.read\_text()
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    importlib.resources: Modern Python resource loading API.
    phlo\_observatory\_example.observatory\_assets: Asset directory contents.
  </Callout>
</PyAttribute>
