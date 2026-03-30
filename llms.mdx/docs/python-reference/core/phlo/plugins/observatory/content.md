# observatory (/docs/python-reference/core/phlo/plugins/observatory)



Core contracts and discovery helpers for Observatory extensions.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ObservatoryExtensionCompatibility&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionCompatibility&#x22;" />

      <Card title="&#x22;ObservatoryExtensionSettings&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionSettings&#x22;" />

      <Card title="&#x22;ObservatoryExtensionRoute&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionRoute&#x22;" />

      <Card title="&#x22;ObservatoryExtensionNavItem&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionNavItem&#x22;" />

      <Card title="&#x22;ObservatoryExtensionSlot&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionSlot&#x22;" />

      <Card title="&#x22;ObservatoryExtensionSettingsPanel&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionSettingsPanel&#x22;" />

      <Card title="&#x22;ObservatoryExtensionUI&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionUI&#x22;" />

      <Card title="&#x22;ObservatoryExtensionManifest&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionManifest&#x22;" />

      <Card title="&#x22;ObservatoryExtensionPlugin&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory/ObservatoryExtensionPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_is_plugin_allowed&#x22;" type="&#x22;(plugin_name) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _is_plugin_allowed(plugin_name: str) -> bool:
            settings = get_settings()
            if plugin_name in settings.plugins_blacklist:
                logger.debug("Plugin '%s' is blacklisted, skipping", plugin_name)
                return False
            if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
                logger.debug("Plugin '%s' is not in whitelist, skipping", plugin_name)
                return False
            return True
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;discover_observatory_extensions&#x22;" type="&#x22;() -> list[ObservatoryExtensionPlugin]&#x22;">
      Discover installed Observatory extension plugins.

      <PySourceCode>
        ```python
        def discover_observatory_extensions() -> list[ObservatoryExtensionPlugin]:
            """Discover installed Observatory extension plugins."""
            settings = get_settings()
            if not settings.plugins_enabled:
                logger.info("Plugin system is disabled")
                return []

            try:
                entry_points = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
            except TypeError:
                entry_points = importlib.metadata.entry_points().get(_ENTRY_POINT_GROUP, [])

            plugins: list[ObservatoryExtensionPlugin] = []
            for entry_point in entry_points:
                if not _is_plugin_allowed(entry_point.name):
                    continue
                try:
                    plugin_class = entry_point.load()
                    plugin = plugin_class() if isinstance(plugin_class, type) else plugin_class
                except Exception as exc:
                    logger.warning("Failed to load Observatory extension %s: %s", entry_point.name, exc)
                    continue
                if not isinstance(plugin, ObservatoryExtensionPlugin):
                    logger.warning(
                        "Observatory extension %s has invalid type %s",
                        entry_point.name,
                        type(plugin).__name__,
                    )
                    continue
                plugins.append(plugin)

            return plugins
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[phlo.plugins.observatory.ObservatoryExtensionPlugin]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_observatory_extension&#x22;" type="&#x22;(name) -> ObservatoryExtensionPlugin | None&#x22;">
      Return a single Observatory extension by name.

      <PySourceCode>
        ```python
        def get_observatory_extension(name: str) -> ObservatoryExtensionPlugin | None:
            """Return a single Observatory extension by name."""
            for plugin in discover_observatory_extensions():
                if plugin.metadata.name == name:
                    return plugin
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.plugins.observatory.ObservatoryExtensionPlugin | None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
