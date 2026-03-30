# LineageObservatoryExtension (/docs/python-reference/packages/phlo-lineage/phlo_lineage/observatory_plugin/LineageObservatoryExtension)



Observatory extension metadata for lineage graph UI.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for extension discovery.

  Provides identifying information for the Observatory plugin system
  to recognize and load this extension.

  Discovery:
  This metadata is used by the Observatory plugin loader to:

  * Identify the extension uniquely
  * Display extension information in the UI
  * Check for duplicate or conflicting extensions

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > ext = LineageObservatoryExtension()
    > > > meta = ext.metadata
    > > > print(f"Extension: \{meta.name} v\{meta.version}")
    > > > Extension: lineage v0.1.0
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;manifest&#x22;" type="&#x22;ObservatoryExtensionManifest&#x22;" value="null">
  Return Observatory extension manifest configuration.

  Defines the extension's UI integration points, version compatibility
  requirements, and navigation structure within Observatory.

  Manifest Contents:

  * name: "lineage" (must match metadata.name)
  * version: "0.1.0"
  * compat.observatory\_min: "0.1.0" (minimum Observatory version)
  * ui.nav: \[NavItem(title="Lineage Graph", to="/graph")]

  Compatibility:
  The extension requires Observatory core version >= 0.1.0.
  Loading in incompatible versions will raise a warning.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > ext = LineageObservatoryExtension()
    > > > manifest = ext.manifest
    > > > print(f"Requires Observatory >= \{manifest.compat.observatory\_min}")
    > > > for item in manifest.ui.nav:
    > > > ...     print(f"Nav: \{item.title} -> \{item.to}")
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    ObservatoryExtensionManifest for full manifest schema.
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;asset_root&#x22;" type="&#x22;Traversable&#x22;" value="null">
  Return the static asset directory for the extension.

  Provides access to bundled static assets (JavaScript, CSS, images)
  that are served by the Observatory web server for the lineage UI.

  Asset Types:
  The directory typically contains:

  * JavaScript files for interactive lineage graph visualization
  * CSS stylesheets for lineage-specific styling
  * Image assets for icons and visual elements
  * HTML templates for the lineage graph view

  Serving:
  Observatory serves these assets at a URL path derived from
  the extension name (e.g., /extensions/lineage/assets/).

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > ext = LineageObservatoryExtension()
    > > > assets = ext.asset\_root
    > > >
    > > > List asset files [#list-asset-files]
    > > >
    > > > for path in assets.iterdir():
    > > > ...     print(f"Asset: \{path.name}")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Uses importlib.resources for safe package resource access.
    Works correctly in both development and installed (wheel) contexts.
  </Callout>
</PyAttribute>
