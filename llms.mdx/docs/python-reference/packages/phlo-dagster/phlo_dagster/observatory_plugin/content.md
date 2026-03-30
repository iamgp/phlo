# observatory_plugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/observatory_plugin)



Observatory extension for Dagster assets UI.

This module provides an ObservatoryExtensionPlugin that exposes Dagster
asset information to Phlo's Observatory web UI. It registers the extension
with the Observatory plugin system and provides static assets for the
Dagster assets view.

Observatory Integration:
The DagsterObservatoryExtension implements the ObservatoryExtensionPlugin
interface to contribute:

* Extension metadata (name, version, compatibility)
* Navigation items for the Observatory UI
* Static assets (HTML, JS, CSS) for the assets view

Extension Points:

* metadata: Plugin identity for discovery
* manifest: Extension manifest with navigation and compatibility
* asset\_root: Package path to bundled UI assets

UI Assets:
Static assets are bundled in the package under observatory\_assets/ and
served through the Observatory's static file handling.

Navigation:
The extension adds an "Assets" navigation item linking to /assets view
that renders the Dagster assets UI.

Example:
Extension registration via entry\_points::

\[phlo.plugins.observatory]
dagster = phlo\_dagster.observatory\_plugin:DagsterObservatoryExtension

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterObservatoryExtension&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/observatory_plugin/DagsterObservatoryExtension&#x22;" />
    </Cards>
  </Tab>
</Tabs>
