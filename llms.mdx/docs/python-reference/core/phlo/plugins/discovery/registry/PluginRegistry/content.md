# PluginRegistry (/docs/python-reference/core/phlo/plugins/discovery/registry/PluginRegistry)



Central registry for Phlo plugins.

The registry maintains separate catalogs for each plugin type
and provides methods for registering and retrieving plugins.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self)&#x22;">
  Initialize empty plugin registry.

  <PySourceCode>
    ```python
    def __init__(self):
        """Initialize empty plugin registry."""
        self._sources: dict[str, SourceConnectorPlugin] = {}
        self._quality_checks: dict[str, QualityCheckPlugin] = {}
        self._quality_providers: dict[str, QualityProviderPlugin] = {}
        self._ingestion_providers: dict[str, IngestionProviderPlugin] = {}
        self._transformation_providers: dict[str, TransformationProviderPlugin] = {}
        self._transformations: dict[str, TransformationPlugin] = {}
        self._services: dict[str, ServicePlugin] = {}
        self._cli_commands: dict[str, CliCommandPlugin] = {}
        self._hooks: dict[str, HookPlugin] = {}
        self._assets: dict[str, AssetProviderPlugin] = {}
        self._resources: dict[str, ResourceProviderPlugin] = {}
        self._orchestrators: dict[str, OrchestratorAdapterPlugin] = {}
        self._catalogs: dict[str, CatalogPlugin] = {}
        self._all_plugins: dict[str, Plugin] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_register_plugin&#x22;" type="&#x22;(self, plugin_type, plugin, replace=False) -> None&#x22;">
  Register a plugin of any type.

  <PySourceCode>
    ```python
    def _register_plugin(self, plugin_type: str, plugin: Plugin, replace: bool = False) -> None:
        """Register a plugin of any type."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            logger.error("plugin_registration_unknown_type", plugin_type=plugin_type)
            raise ValueError(f"Unknown plugin type: {plugin_type}")

        dict_name, key_prefix, type_label = config
        plugin_dict = getattr(self, dict_name)
        name = plugin.metadata.name

        if name in plugin_dict and not replace:
            logger.warning(
                "plugin_registration_conflict",
                plugin_type=plugin_type,
                plugin_name=name,
            )
            raise ValueError(
                f"{type_label} plugin '{name}' is already registered. "
                f"Use replace=True to overwrite."
            )

        plugin_dict[name] = plugin
        self._all_plugins[f"{key_prefix}:{name}"] = plugin
        logger.debug(
            "plugin_registered",
            plugin_type=plugin_type,
            plugin_name=name,
            replace=replace,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Plugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_source_connector&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a source connector plugin.

  <PySourceCode>
    ```python
    def register_source_connector(
        self, plugin: SourceConnectorPlugin, replace: bool = False
    ) -> None:
        """Register a source connector plugin."""
        self._register_plugin("source_connectors", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;SourceConnectorPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_quality_check&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a quality check plugin.

  <PySourceCode>
    ```python
    def register_quality_check(self, plugin: QualityCheckPlugin, replace: bool = False) -> None:
        """Register a quality check plugin."""
        self._register_plugin("quality_checks", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;QualityCheckPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_quality_provider&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a quality provider plugin.

  <PySourceCode>
    ```python
    def register_quality_provider(
        self, plugin: QualityProviderPlugin, replace: bool = False
    ) -> None:
        """Register a quality provider plugin."""
        self._register_plugin("quality_providers", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;QualityProviderPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_ingestion_provider&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register an ingestion provider plugin.

  <PySourceCode>
    ```python
    def register_ingestion_provider(
        self, plugin: IngestionProviderPlugin, replace: bool = False
    ) -> None:
        """Register an ingestion provider plugin."""
        self._register_plugin("ingestion_providers", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;IngestionProviderPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_transformation_provider&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a transformation provider plugin.

  <PySourceCode>
    ```python
    def register_transformation_provider(
        self, plugin: TransformationProviderPlugin, replace: bool = False
    ) -> None:
        """Register a transformation provider plugin."""
        self._register_plugin("transformation_providers", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;TransformationProviderPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_transformation&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a transformation plugin.

  <PySourceCode>
    ```python
    def register_transformation(self, plugin: TransformationPlugin, replace: bool = False) -> None:
        """Register a transformation plugin."""
        self._register_plugin("transformations", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;TransformationPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_service&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a service plugin.

  <PySourceCode>
    ```python
    def register_service(self, plugin: ServicePlugin, replace: bool = False) -> None:
        """Register a service plugin."""
        self._register_plugin("services", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;ServicePlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_cli_command_plugin&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a CLI command plugin.

  <PySourceCode>
    ```python
    def register_cli_command_plugin(self, plugin: CliCommandPlugin, replace: bool = False) -> None:
        """Register a CLI command plugin."""
        self._register_plugin("cli_commands", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;CliCommandPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_hook_plugin&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a hook plugin.

  <PySourceCode>
    ```python
    def register_hook_plugin(self, plugin: HookPlugin, replace: bool = False) -> None:
        """Register a hook plugin."""
        self._register_plugin("hooks", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;HookPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_asset_provider&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register an asset provider plugin.

  <PySourceCode>
    ```python
    def register_asset_provider(self, plugin: AssetProviderPlugin, replace: bool = False) -> None:
        """Register an asset provider plugin."""
        self._register_plugin("asset_providers", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;AssetProviderPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_resource_provider&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a resource provider plugin.

  <PySourceCode>
    ```python
    def register_resource_provider(
        self, plugin: ResourceProviderPlugin, replace: bool = False
    ) -> None:
        """Register a resource provider plugin."""
        self._register_plugin("resource_providers", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;ResourceProviderPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_orchestrator&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register an orchestrator adapter plugin.

  <PySourceCode>
    ```python
    def register_orchestrator(
        self, plugin: OrchestratorAdapterPlugin, replace: bool = False
    ) -> None:
        """Register an orchestrator adapter plugin."""
        self._register_plugin("orchestrators", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;OrchestratorAdapterPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_catalog&#x22;" type="&#x22;(self, plugin, replace=False) -> None&#x22;">
  Register a catalog plugin.

  <PySourceCode>
    ```python
    def register_catalog(self, plugin: CatalogPlugin, replace: bool = False) -> None:
        """Register a catalog plugin."""
        self._register_plugin("catalogs", plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;CatalogPlugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get&#x22;" type="&#x22;(self, plugin_type, name) -> Plugin | None&#x22;">
  Get a plugin by type and name.

  <PySourceCode>
    ```python
    def get(self, plugin_type: str, name: str) -> Plugin | None:
        """Get a plugin by type and name."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            return None
        return getattr(self, config[0]).get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.Plugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list&#x22;" type="&#x22;(self, plugin_type) -> list[str]&#x22;">
  List all plugins of a given type.

  <PySourceCode>
    ```python
    def list(self, plugin_type: str) -> list[str]:
        """List all plugins of a given type."""
        config = _TYPE_CONFIG.get(plugin_type)
        if not config:
            return []
        return list(getattr(self, config[0]).keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register&#x22;" type="&#x22;(self, plugin_type, plugin, replace=False) -> None&#x22;">
  Register a plugin of any type (alias for \_register\_plugin).

  <PySourceCode>
    ```python
    def register(self, plugin_type: str, plugin: Plugin, replace: bool = False) -> None:
        """Register a plugin of any type (alias for _register_plugin)."""
        self._register_plugin(plugin_type, plugin, replace)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Plugin&#x22;" value="null" />

    <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_source_connector&#x22;" type="&#x22;(self, name) -> SourceConnectorPlugin | None&#x22;">
  Get a source connector plugin by name.

  <PySourceCode>
    ```python
    def get_source_connector(self, name: str) -> SourceConnectorPlugin | None:
        """Get a source connector plugin by name."""
        return self._sources.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.SourceConnectorPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_quality_check&#x22;" type="&#x22;(self, name) -> QualityCheckPlugin | None&#x22;">
  Get a quality check plugin by name.

  <PySourceCode>
    ```python
    def get_quality_check(self, name: str) -> QualityCheckPlugin | None:
        """Get a quality check plugin by name."""
        return self._quality_checks.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.QualityCheckPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_quality_provider&#x22;" type="&#x22;(self, name) -> QualityProviderPlugin | None&#x22;">
  Get a quality provider plugin by name.

  <PySourceCode>
    ```python
    def get_quality_provider(self, name: str) -> QualityProviderPlugin | None:
        """Get a quality provider plugin by name."""
        return self._quality_providers.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.QualityProviderPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_ingestion_provider&#x22;" type="&#x22;(self, name) -> IngestionProviderPlugin | None&#x22;">
  Get an ingestion provider plugin by name.

  <PySourceCode>
    ```python
    def get_ingestion_provider(self, name: str) -> IngestionProviderPlugin | None:
        """Get an ingestion provider plugin by name."""
        return self._ingestion_providers.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.IngestionProviderPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_transformation_provider&#x22;" type="&#x22;(self, name) -> TransformationProviderPlugin | None&#x22;">
  Get a transformation provider plugin by name.

  <PySourceCode>
    ```python
    def get_transformation_provider(self, name: str) -> TransformationProviderPlugin | None:
        """Get a transformation provider plugin by name."""
        return self._transformation_providers.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.TransformationProviderPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_transformation&#x22;" type="&#x22;(self, name) -> TransformationPlugin | None&#x22;">
  Get a transformation plugin by name.

  <PySourceCode>
    ```python
    def get_transformation(self, name: str) -> TransformationPlugin | None:
        """Get a transformation plugin by name."""
        return self._transformations.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.TransformationPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_service&#x22;" type="&#x22;(self, name) -> ServicePlugin | None&#x22;">
  Get a service plugin by name.

  <PySourceCode>
    ```python
    def get_service(self, name: str) -> ServicePlugin | None:
        """Get a service plugin by name."""
        return self._services.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.ServicePlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_cli_command_plugin&#x22;" type="&#x22;(self, name) -> CliCommandPlugin | None&#x22;">
  Get a CLI command plugin by name.

  <PySourceCode>
    ```python
    def get_cli_command_plugin(self, name: str) -> CliCommandPlugin | None:
        """Get a CLI command plugin by name."""
        return self._cli_commands.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.CliCommandPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_hook_plugin&#x22;" type="&#x22;(self, name) -> HookPlugin | None&#x22;">
  Get a hook plugin by name.

  <PySourceCode>
    ```python
    def get_hook_plugin(self, name: str) -> HookPlugin | None:
        """Get a hook plugin by name."""
        return self._hooks.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.hooks.HookPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_asset_provider&#x22;" type="&#x22;(self, name) -> AssetProviderPlugin | None&#x22;">
  Get an asset provider plugin by name.

  <PySourceCode>
    ```python
    def get_asset_provider(self, name: str) -> AssetProviderPlugin | None:
        """Get an asset provider plugin by name."""
        return self._assets.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.AssetProviderPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_resource_provider&#x22;" type="&#x22;(self, name) -> ResourceProviderPlugin | None&#x22;">
  Get a resource provider plugin by name.

  <PySourceCode>
    ```python
    def get_resource_provider(self, name: str) -> ResourceProviderPlugin | None:
        """Get a resource provider plugin by name."""
        return self._resources.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.ResourceProviderPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_orchestrator&#x22;" type="&#x22;(self, name) -> OrchestratorAdapterPlugin | None&#x22;">
  Get an orchestrator adapter plugin by name.

  <PySourceCode>
    ```python
    def get_orchestrator(self, name: str) -> OrchestratorAdapterPlugin | None:
        """Get an orchestrator adapter plugin by name."""
        return self._orchestrators.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.OrchestratorAdapterPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_catalog&#x22;" type="&#x22;(self, name) -> CatalogPlugin | None&#x22;">
  Get a catalog plugin by name.

  <PySourceCode>
    ```python
    def get_catalog(self, name: str) -> CatalogPlugin | None:
        """Get a catalog plugin by name."""
        return self._catalogs.get(name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.base.CatalogPlugin | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_source_connectors&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered source connector plugins.

  <PySourceCode>
    ```python
    def list_source_connectors(self) -> list[str]:
        """List all registered source connector plugins."""
        return list(self._sources.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_quality_checks&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered quality check plugins.

  <PySourceCode>
    ```python
    def list_quality_checks(self) -> list[str]:
        """List all registered quality check plugins."""
        return list(self._quality_checks.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_quality_providers&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered quality provider plugins.

  <PySourceCode>
    ```python
    def list_quality_providers(self) -> list[str]:
        """List all registered quality provider plugins."""
        return list(self._quality_providers.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_ingestion_providers&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered ingestion provider plugins.

  <PySourceCode>
    ```python
    def list_ingestion_providers(self) -> list[str]:
        """List all registered ingestion provider plugins."""
        return list(self._ingestion_providers.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_transformation_providers&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered transformation provider plugins.

  <PySourceCode>
    ```python
    def list_transformation_providers(self) -> list[str]:
        """List all registered transformation provider plugins."""
        return list(self._transformation_providers.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_transformations&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered transformation plugins.

  <PySourceCode>
    ```python
    def list_transformations(self) -> list[str]:
        """List all registered transformation plugins."""
        return list(self._transformations.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_services&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered service plugins.

  <PySourceCode>
    ```python
    def list_services(self) -> list[str]:
        """List all registered service plugins."""
        return list(self._services.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_cli_command_plugins&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered CLI command plugins.

  <PySourceCode>
    ```python
    def list_cli_command_plugins(self) -> list[str]:
        """List all registered CLI command plugins."""
        return list(self._cli_commands.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_hook_plugins&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered hook plugins.

  <PySourceCode>
    ```python
    def list_hook_plugins(self) -> list[str]:
        """List all registered hook plugins."""
        return list(self._hooks.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_asset_providers&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered asset provider plugins.

  <PySourceCode>
    ```python
    def list_asset_providers(self) -> list[str]:
        """List all registered asset provider plugins."""
        return list(self._assets.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_resource_providers&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered resource provider plugins.

  <PySourceCode>
    ```python
    def list_resource_providers(self) -> list[str]:
        """List all registered resource provider plugins."""
        return list(self._resources.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_orchestrators&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered orchestrator adapter plugins.

  <PySourceCode>
    ```python
    def list_orchestrators(self) -> list[str]:
        """List all registered orchestrator adapter plugins."""
        return list(self._orchestrators.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_catalogs&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all registered catalog plugins.

  <PySourceCode>
    ```python
    def list_catalogs(self) -> list[str]:
        """List all registered catalog plugins."""
        return list(self._catalogs.keys())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_all_plugins&#x22;" type="&#x22;(self) -> dict[str, list[str]]&#x22;">
  List all registered plugins by type.

  <PySourceCode>
    ```python
    def list_all_plugins(self) -> dict[str, list[str]]:
        """List all registered plugins by type."""
        return {ptype: self.list(ptype) for ptype in _TYPE_CONFIG}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict[str, phlo.plugins.discovery.registry.PluginRegistry.list[str]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;clear&#x22;" type="&#x22;(self) -> None&#x22;">
  Clear all registered plugins.

  <PySourceCode>
    ```python
    def clear(self) -> None:
        """Clear all registered plugins."""
        total = len(self._all_plugins)
        cleaned = 0
        cleanup_failures = 0
        cleaned_plugin_ids: set[int] = set()

        for plugin_key, plugin in list(self._all_plugins.items()):
            plugin_id = id(plugin)
            if plugin_id in cleaned_plugin_ids:
                continue
            cleaned_plugin_ids.add(plugin_id)
            try:
                plugin.cleanup()
                cleaned += 1
            except Exception:
                cleanup_failures += 1
                logger.warning("plugin_cleanup_failed", plugin_key=plugin_key, exc_info=True)

        for config in _TYPE_CONFIG.values():
            getattr(self, config[0]).clear()
        self._all_plugins.clear()
        logger.debug(
            "plugin_registry_cleared",
            previous_total=total,
            unique_plugins=len(cleaned_plugin_ids),
            cleaned_plugins=cleaned,
            cleanup_failures=cleanup_failures,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;iter_plugins&#x22;" type="&#x22;(self) -> list[Plugin]&#x22;">
  Return all registered plugin instances.

  <PySourceCode>
    ```python
    def iter_plugins(self) -> list[Plugin]:
        """Return all registered plugin instances."""
        return list(self._all_plugins.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.discovery.registry.PluginRegistry.list[phlo.plugins.base.Plugin]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__len__&#x22;" type="&#x22;(self) -> int&#x22;">
  Return total number of registered plugins.

  <PySourceCode>
    ```python
    def __len__(self) -> int:
        """Return total number of registered plugins."""
        return len(self._all_plugins)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;int&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__contains__&#x22;" type="&#x22;(self, key) -> bool&#x22;">
  Check if a plugin is registered (key format: 'type:name').

  <PySourceCode>
    ```python
    def __contains__(self, key: str) -> bool:
        """Check if a plugin is registered (key format: 'type:name')."""
        return key in self._all_plugins
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;key&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_plugin_metadata&#x22;" type="&#x22;(self, plugin_type, name) -> dict | None&#x22;">
  Get metadata for a plugin by type and name.

  <PySourceCode>
    ```python
    def get_plugin_metadata(self, plugin_type: str, name: str) -> dict | None:
        """
        Get metadata for a plugin by type and name.

        Args:
            plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
                "services", "catalogs")
            name: Plugin name

        Returns:
            Dictionary with plugin metadata or None if not found
        """
        plugin = self.get(plugin_type, name)
        if not plugin:
            return None

        metadata = plugin.metadata
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "author": metadata.author,
            "license": metadata.license,
            "homepage": metadata.homepage,
            "tags": metadata.tags,
            "dependencies": metadata.dependencies,
            "requires_capabilities": metadata.requires_capabilities,
            "optional_capabilities": metadata.optional_capabilities,
            "support": metadata.support.to_dict(),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="undefined">
      Plugin type ("source\_connectors", "quality\_checks", "transformations",
      "services", "catalogs")
    </PyParameter>

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Plugin name
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict | None&#x22;">
    Dictionary with plugin metadata or None if not found
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;validate_plugin&#x22;" type="&#x22;(self, plugin) -> bool&#x22;">
  Validate plugin interface compliance.

  <PySourceCode>
    ```python
    def validate_plugin(self, plugin: Plugin) -> bool:
        """
        Validate plugin interface compliance.

        Args:
            plugin: Plugin instance to validate

        Returns:
            True if plugin is valid, False otherwise
        """
        # Check required attributes
        if not hasattr(plugin, "metadata"):
            return False

        try:
            metadata = plugin.metadata
            # Check required metadata fields
            if not all(hasattr(metadata, f) for f in ("name", "version")):
                return False
        except Exception:
            logger.debug("plugin_validation_metadata_access_failed", exc_info=True)
            return False

        # Type-specific validation
        if isinstance(plugin, SourceConnectorPlugin):
            return hasattr(plugin, "fetch_data") and callable(plugin.fetch_data)
        if isinstance(plugin, QualityCheckPlugin):
            return hasattr(plugin, "create_check") and callable(plugin.create_check)
        if isinstance(plugin, TransformationPlugin):
            return hasattr(plugin, "transform") and callable(plugin.transform)
        if isinstance(plugin, ServicePlugin):
            try:
                service_definition = plugin.service_definition
            except Exception:
                logger.debug("plugin_validation_service_definition_failed", exc_info=True)
                return False
            return isinstance(service_definition, dict)
        if isinstance(plugin, HookPlugin):
            return hasattr(plugin, "get_hooks") and callable(plugin.get_hooks)
        if isinstance(plugin, AssetProviderPlugin):
            return hasattr(plugin, "get_assets") and callable(plugin.get_assets)
        if isinstance(plugin, ResourceProviderPlugin):
            return hasattr(plugin, "get_resources") and callable(plugin.get_resources)
        if isinstance(plugin, OrchestratorAdapterPlugin):
            return hasattr(plugin, "build_definitions") and callable(plugin.build_definitions)
        if isinstance(plugin, CatalogPlugin):
            has_catalog = hasattr(plugin, "catalog_name")
            has_targets = hasattr(plugin, "targets")
            has_properties = hasattr(plugin, "get_properties") and callable(plugin.get_properties)
            return has_catalog and has_targets and has_properties
        return True
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Plugin&#x22;" value="undefined">
      Plugin instance to validate
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if plugin is valid, False otherwise
  </PyFunctionReturn>
</PyFunction>
