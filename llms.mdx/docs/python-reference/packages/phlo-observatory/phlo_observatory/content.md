# phlo_observatory (/docs/python-reference/packages/phlo-observatory/phlo_observatory)



Phlo Observatory UI package.

The Observatory is Phlo's web-based UI for data observability, lineage visualization,
and system monitoring. This package provides the core infrastructure for the
Observatory web interface, including extension discovery, settings management,
and service orchestration.

Key Components:

* ObservatoryExtensionPlugin: Base class for extending Observatory UI
* ObservatorySettings: Configuration for the Observatory service
* SettingsService: Persistent storage for UI settings and preferences
* ObservatoryServicePlugin: Service plugin for container orchestration

Example:

> > > from phlo\_observatory import ObservatorySettings, get\_settings
> > > settings = get\_settings()
> > > print(settings.observatory\_settings\_db\_url)

See Also:

* phlo.plugins.observatory: Extension API definitions
* phlo.plugins.observatory\_settings: Settings storage backend

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['ObservatoryExtensionCompatibility', 'ObservatoryExtensionManifest', 'ObservatoryExtensionNavItem', 'ObservatoryExtensionPlugin', 'ObservatoryExtensionRoute', 'ObservatoryExtensionSettings', 'ObservatoryExtensionSettingsPanel', 'ObservatoryExtensionSlot', 'ObservatoryExtensionUI', 'ObservatoryServicePlugin', 'ObservatorySettings', 'SettingsRecord', 'SettingsScope', 'SettingsService', 'discover_observatory_extensions', 'get_observatory_extension', 'get_settings', 'get_settings_service']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.3'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings_service&#x22;" title="&#x22;settings_service&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/manifest&#x22;" title="&#x22;manifest&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/extensions&#x22;" title="&#x22;extensions&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/observatory_ext&#x22;" title="&#x22;observatory_ext&#x22;" />
    </Cards>
  </Tab>
</Tabs>
