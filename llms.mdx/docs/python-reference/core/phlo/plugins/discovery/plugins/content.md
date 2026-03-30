# plugins (/docs/python-reference/core/phlo/plugins/discovery/plugins)



Plugin discovery mechanism using Python entry points.

This module discovers and loads plugins from installed Python packages
that declare phlo.plugins entry points.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;ENTRY_POINT_GROUPS&#x22;" type="null" value="&#x22;{'source_connectors': 'phlo.plugins.sources', 'quality_checks': 'phlo.plugins.quality', 'quality_providers': 'phlo.plugins.quality_providers', 'ingestion_providers': 'phlo.plugins.ingestion_providers', 'transformation_providers': 'phlo.plugins.transformation_providers', 'transformations': 'phlo.plugins.transforms', 'services': 'phlo.plugins.services', 'cli_commands': 'phlo.plugins.cli', 'hooks': 'phlo.plugins.hooks', 'catalogs': 'phlo.plugins.catalogs', 'asset_providers': 'phlo.plugins.assets', 'resource_providers': 'phlo.plugins.resources', 'orchestrators': 'phlo.plugins.orchestrators'}&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_is_plugin_allowed&#x22;" type="&#x22;(plugin_name) -> bool&#x22;">
      Check if a plugin is allowed based on whitelist/blacklist configuration.

      <PySourceCode>
        ```python
        def _is_plugin_allowed(plugin_name: str) -> bool:
            """
            Check if a plugin is allowed based on whitelist/blacklist configuration.

            Args:
                plugin_name: Name of the plugin

            Returns:
                True if plugin should be loaded, False otherwise
            """
            settings = get_settings()

            # Check blacklist first
            if plugin_name in settings.plugins_blacklist:
                logger.debug("plugin_blacklisted_skipping", plugin_name=plugin_name)
                return False

            # Check whitelist (if not empty)
            if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
                logger.debug("plugin_not_whitelisted_skipping", plugin_name=plugin_name)
                return False

            return True
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the plugin
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if plugin should be loaded, False otherwise
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_emit_plugin_lifecycle_signal&#x22;" type="&#x22;(*, event_name, level, plugin_type, plugin_name, lifecycle_phase, replace, reason=None, error=None, target_plugin_name=None) -> None&#x22;">
      Emit structured observability signals for plugin lifecycle operations.

      <PySourceCode>
        ```python
        def _emit_plugin_lifecycle_signal(
            *,
            event_name: str,
            level: str,
            plugin_type: str,
            plugin_name: str,
            lifecycle_phase: str,
            replace: bool,
            reason: str | None = None,
            error: Exception | None = None,
            target_plugin_name: str | None = None,
        ) -> None:
            """Emit structured observability signals for plugin lifecycle operations."""
            fields: dict[str, Any] = {
                "plugin_type": plugin_type,
                "plugin_name": plugin_name,
                "lifecycle_phase": lifecycle_phase,
                "replace": replace,
            }
            if reason is not None:
                fields["reason"] = reason
            if target_plugin_name is not None:
                fields["target_plugin_name"] = target_plugin_name
            if error is not None:
                fields["error"] = str(error)
                fields["error_type"] = type(error).__name__
            log_event(logger, level, event_name, **fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;event_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;lifecycle_phase&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;reason&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;error&#x22;" type="&#x22;Exception | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;target_plugin_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_register_plugin_with_lifecycle&#x22;" type="&#x22;(plugin_type, plugin, replace=True) -> None&#x22;">
      Register plugin with initialize/cleanup lifecycle hooks and rollback safeguards.

      <PySourceCode>
        ```python
        def _register_plugin_with_lifecycle(plugin_type: str, plugin: Plugin, replace: bool = True) -> None:
            """Register plugin with initialize/cleanup lifecycle hooks and rollback safeguards."""
            registry = get_global_registry()
            register_method_name = _PLUGIN_REGISTER_METHODS.get(plugin_type)
            getter_method_name = _PLUGIN_GETTER_METHODS.get(plugin_type)

            if not register_method_name or not getter_method_name:
                raise ValueError(f"Unknown plugin type: {plugin_type}")

            register_method = getattr(registry, register_method_name)
            plugin_name = plugin.metadata.name
            existing_plugin = getattr(registry, getter_method_name)(plugin_name)

            # Let registry raise duplicate registration errors without initializing a plugin that
            # cannot be registered.
            if existing_plugin and not replace:
                register_method(plugin, replace=False)
                return

            try:
                plugin.initialize({})
                _emit_plugin_lifecycle_signal(
                    event_name="plugin_lifecycle_initialize_succeeded",
                    level="debug",
                    plugin_type=plugin_type,
                    plugin_name=plugin_name,
                    lifecycle_phase="incoming_plugin_initialize",
                    replace=replace,
                )
            except Exception as exc:
                _emit_plugin_lifecycle_signal(
                    event_name="plugin_lifecycle_initialize_failed",
                    level="error",
                    plugin_type=plugin_type,
                    plugin_name=plugin_name,
                    lifecycle_phase="incoming_plugin_initialize",
                    replace=replace,
                    error=exc,
                )
                try:
                    plugin.cleanup()
                    _emit_plugin_lifecycle_signal(
                        event_name="plugin_lifecycle_cleanup_succeeded",
                        level="info",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        lifecycle_phase="incoming_plugin_cleanup",
                        replace=replace,
                        reason="initialize_failed",
                    )
                except Exception as cleanup_exc:
                    _emit_plugin_lifecycle_signal(
                        event_name="plugin_lifecycle_cleanup_failed",
                        level="error",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        lifecycle_phase="incoming_plugin_cleanup",
                        replace=replace,
                        reason="initialize_failed",
                        error=cleanup_exc,
                    )
                    logger.warning(
                        "plugin_cleanup_after_initialize_failed",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        exc_info=True,
                    )
                raise

            existing_cleaned = False
            existing_plugin_name = existing_plugin.metadata.name if existing_plugin else None
            try:
                if existing_plugin and replace:
                    try:
                        existing_plugin.cleanup()
                        _emit_plugin_lifecycle_signal(
                            event_name="plugin_lifecycle_cleanup_succeeded",
                            level="debug",
                            plugin_type=plugin_type,
                            plugin_name=existing_plugin_name or plugin_name,
                            lifecycle_phase="existing_plugin_cleanup",
                            replace=replace,
                            reason="replacement",
                            target_plugin_name=plugin_name,
                        )
                        existing_cleaned = True
                    except Exception as exc:
                        _emit_plugin_lifecycle_signal(
                            event_name="plugin_lifecycle_cleanup_failed",
                            level="error",
                            plugin_type=plugin_type,
                            plugin_name=existing_plugin_name or plugin_name,
                            lifecycle_phase="existing_plugin_cleanup",
                            replace=replace,
                            reason="replacement",
                            target_plugin_name=plugin_name,
                            error=exc,
                        )
                        raise
                register_method(plugin, replace=replace)
            except Exception:
                if existing_cleaned:
                    assert existing_plugin is not None
                    try:
                        existing_plugin.initialize({})
                        _emit_plugin_lifecycle_signal(
                            event_name="plugin_lifecycle_initialize_succeeded",
                            level="debug",
                            plugin_type=plugin_type,
                            plugin_name=existing_plugin_name or plugin_name,
                            lifecycle_phase="existing_plugin_recovery_initialize",
                            replace=replace,
                            reason="registration_failed_rollback",
                            target_plugin_name=plugin_name,
                        )
                    except Exception as recovery_exc:
                        _emit_plugin_lifecycle_signal(
                            event_name="plugin_lifecycle_initialize_failed",
                            level="error",
                            plugin_type=plugin_type,
                            plugin_name=existing_plugin_name or plugin_name,
                            lifecycle_phase="existing_plugin_recovery_initialize",
                            replace=replace,
                            reason="registration_failed_rollback",
                            target_plugin_name=plugin_name,
                            error=recovery_exc,
                        )
                        logger.error(
                            "plugin_recovery_initialize_failed",
                            plugin_type=plugin_type,
                            plugin_name=plugin_name,
                            exc_info=True,
                        )
                try:
                    plugin.cleanup()
                    _emit_plugin_lifecycle_signal(
                        event_name="plugin_lifecycle_cleanup_succeeded",
                        level="info",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        lifecycle_phase="incoming_plugin_cleanup",
                        replace=replace,
                        reason="registration_failed",
                    )
                except Exception as cleanup_exc:
                    _emit_plugin_lifecycle_signal(
                        event_name="plugin_lifecycle_cleanup_failed",
                        level="error",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        lifecycle_phase="incoming_plugin_cleanup",
                        replace=replace,
                        reason="registration_failed",
                        error=cleanup_exc,
                    )
                    logger.warning(
                        "plugin_cleanup_after_registration_failed",
                        plugin_type=plugin_type,
                        plugin_name=plugin_name,
                        exc_info=True,
                    )
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;plugin&#x22;" type="&#x22;Plugin&#x22;" value="null" />

        <PyParameter name="&#x22;replace&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;discover_plugins&#x22;" type="&#x22;(plugin_type=None, auto_register=True, *, failure_level='error') -> dict[str, list[Plugin]]&#x22;">
      Discover all installed Phlo plugins.

      This function scans installed Python packages for phlo.plugins
      entry points and loads the plugins.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        # Discover all plugins
        plugins = discover_plugins()
        # \{'source_connectors': [...], 'quality_checks': [...], ...\}

        # Discover only source connectors
        sources = discover_plugins(plugin_type="source_connectors")
        # \{'source_connectors': [...]\}
        ```
      </Callout>

      <PySourceCode>
        ````python
        def discover_plugins(
            plugin_type: str | None = None,
            auto_register: bool = True,
            *,
            failure_level: str = "error",
        ) -> dict[str, list[Plugin]]:
            """
            Discover all installed Phlo plugins.

            This function scans installed Python packages for phlo.plugins
            entry points and loads the plugins.

            Args:
                plugin_type: Optional plugin type to discover ("source_connectors",
                    "quality_checks", "transformations", "services", "catalogs"). If None, discover all types.
                auto_register: If True, automatically register discovered plugins
                    in the global registry (default: True)
                failure_level: Log level for plugin import failures. Defaults to ``"error"``.

            Returns:
                Dictionary mapping plugin type to list of discovered plugins

            Example:
                \```python
                # Discover all plugins
                plugins = discover_plugins()
                # {'source_connectors': [...], 'quality_checks': [...], ...}

                # Discover only source connectors
                sources = discover_plugins(plugin_type="source_connectors")
                # {'source_connectors': [...]}
                \```
            """
            settings = get_settings()

            with suppress_log_routing():
                # Check if plugins are enabled
                if not settings.plugins_enabled:
                    logger.info("Plugin system is disabled")
                    return {k: [] for k in ENTRY_POINT_GROUPS}

                discovered: dict[str, list[Plugin]] = {k: [] for k in ENTRY_POINT_GROUPS}

                # Determine which plugin types to discover
                types_to_discover = [plugin_type] if plugin_type else list(ENTRY_POINT_GROUPS.keys())

                for ptype in types_to_discover:
                    if ptype not in ENTRY_POINT_GROUPS:
                        logger.warning("unknown_plugin_type", plugin_type=ptype)
                        continue

                    entry_point_group = ENTRY_POINT_GROUPS[ptype]

                    logger.debug(
                        "plugin_discovery_started",
                        plugin_type=ptype,
                        entry_point_group=entry_point_group,
                    )

                    # Discover entry points
                    try:
                        entry_points = importlib.metadata.entry_points(group=entry_point_group)
                    except TypeError:
                        # Python 3.9 compatibility - entry_points() returns dict
                        all_entry_points = importlib.metadata.entry_points()
                        entry_points = all_entry_points.get(entry_point_group, [])

                    # Load each plugin
                    for entry_point in entry_points:
                        try:
                            # Check if plugin is allowed
                            if not _is_plugin_allowed(entry_point.name):
                                continue

                            logger.debug(
                                "plugin_loading",
                                plugin_name=entry_point.name,
                                entry_point=entry_point.value,
                            )

                            # Load the plugin class
                            plugin_class = entry_point.load()

                            # Instantiate the plugin
                            plugin = plugin_class() if isinstance(plugin_class, type) else plugin_class

                            # Validate plugin type
                            if not isinstance(plugin, Plugin):
                                logger.error(
                                    "plugin_invalid_base_class",
                                    plugin_name=entry_point.name,
                                )
                                continue

                            # Validate specific plugin type
                            expected_type = _PLUGIN_EXPECTED_TYPES[ptype]

                            if not isinstance(plugin, expected_type):
                                logger.error(
                                    "plugin_incorrect_type",
                                    plugin_name=entry_point.name,
                                    expected_type=expected_type.__name__,
                                    actual_type=type(plugin).__name__,
                                )
                                continue

                            if auto_register:
                                _register_plugin_with_lifecycle(ptype, plugin, replace=True)

                            # Add to discovered plugins
                            discovered[ptype].append(plugin)

                            logger.debug(
                                "plugin_loaded",
                                plugin_name=plugin.metadata.name,
                                plugin_version=plugin.metadata.version,
                                plugin_type=ptype,
                            )

                        except Exception:
                            log_method = getattr(logger, failure_level, logger.error)
                            log_method(
                                "plugin_load_failed",
                                plugin_name=entry_point.name,
                                entry_point=entry_point.value,
                                plugin_type=ptype,
                                exc_info=True,
                            )
                            continue

                # Log summary
                total = sum(len(plugins) for plugins in discovered.values())
                logger.debug("plugin_discovery_completed", total_plugins=total, discovered=discovered)

                return discovered
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional plugin type to discover ("source\_connectors",
          "quality\_checks", "transformations", "services", "catalogs"). If None, discover all types.
        </PyParameter>

        <PyParameter name="&#x22;auto_register&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          If True, automatically register discovered plugins
          in the global registry (default: True)
        </PyParameter>

        <PyParameter name="&#x22;failure_level&#x22;" type="&#x22;str&#x22;" value="&#x22;'error'&#x22;">
          Log level for plugin import failures. Defaults to `"error"`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary mapping plugin type to list of discovered plugins
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;list_plugins&#x22;" type="&#x22;(plugin_type=None) -> dict[str, list[str]]&#x22;">
      List all plugins in the global registry.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        # List all plugins
        all_plugins = list_plugins()
        # \{'source_connectors': ['github', 'weather_api'], ...\}

        # List only source connectors
        sources = list_plugins(plugin_type="source_connectors")
        # \{'source_connectors': ['github', 'weather_api']\}
        ```
      </Callout>

      <PySourceCode>
        ````python
        def list_plugins(plugin_type: str | None = None) -> dict[str, list[str]]:
            """
            List all plugins in the global registry.

            Args:
                plugin_type: Optional plugin type to list ("source_connectors",
                    "quality_checks", "transformations", "services", "catalogs"). If None, list all types.

            Returns:
                Dictionary mapping plugin type to list of plugin names

            Example:
                \```python
                # List all plugins
                all_plugins = list_plugins()
                # {'source_connectors': ['github', 'weather_api'], ...}

                # List only source connectors
                sources = list_plugins(plugin_type="source_connectors")
                # {'source_connectors': ['github', 'weather_api']}
                \```
            """
            registry = get_global_registry()
            all_plugins = registry.list_all_plugins()

            if plugin_type:
                if plugin_type not in all_plugins:
                    return {plugin_type: []}
                return {plugin_type: all_plugins[plugin_type]}

            return all_plugins
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional plugin type to list ("source\_connectors",
          "quality\_checks", "transformations", "services", "catalogs"). If None, list all types.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary mapping plugin type to list of plugin names
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_plugin&#x22;" type="&#x22;(plugin_type, name) -> Plugin | None&#x22;">
      Get a plugin by type and name.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        plugin = get_plugin("source_connectors", "github")
        if plugin:
            data = plugin.fetch_data(config=\{...\})
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_plugin(plugin_type: str, name: str) -> Plugin | None:
            """
            Get a plugin by type and name.

            Args:
                plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
                "services", "cli_commands", "hooks", "asset_providers", "resource_providers",
                "orchestrators", "catalogs")
                name: Plugin name

            Returns:
                Plugin instance or None if not found

            Example:
                \```python
                plugin = get_plugin("source_connectors", "github")
                if plugin:
                    data = plugin.fetch_data(config={...})
                \```
            """
            getter_method = _PLUGIN_GETTER_METHODS.get(plugin_type)
            if not getter_method:
                logger.warning("unknown_plugin_type", plugin_type=plugin_type)
                return None
            registry = get_global_registry()
            return getattr(registry, getter_method)(name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin type ("source\_connectors", "quality\_checks", "transformations",
        </PyParameter>

        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;Plugin | None&#x22;">
        Plugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_source_connector&#x22;" type="&#x22;(name) -> SourceConnectorPlugin | None&#x22;">
      Get a source connector plugin by name.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        github = get_source_connector("github")
        if github:
            events = github.fetch_data(config=\{"repo": "owner/repo"\})
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_source_connector(name: str) -> SourceConnectorPlugin | None:
            """
            Get a source connector plugin by name.

            Args:
                name: Plugin name

            Returns:
                SourceConnectorPlugin instance or None if not found

            Example:
                \```python
                github = get_source_connector("github")
                if github:
                    events = github.fetch_data(config={"repo": "owner/repo"})
                \```
            """
            registry = get_global_registry()
            return registry.get_source_connector(name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;SourceConnectorPlugin | None&#x22;">
        SourceConnectorPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_quality_check&#x22;" type="&#x22;(name) -> QualityCheckPlugin | None&#x22;">
      Get a quality check plugin by name.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        custom_check = get_quality_check("business_rule")
        if custom_check:
            check = custom_check.create_check(rule="revenue > 0")
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_quality_check(name: str) -> QualityCheckPlugin | None:
            """
            Get a quality check plugin by name.

            Args:
                name: Plugin name

            Returns:
                QualityCheckPlugin instance or None if not found

            Example:
                \```python
                custom_check = get_quality_check("business_rule")
                if custom_check:
                    check = custom_check.create_check(rule="revenue > 0")
                \```
            """
            registry = get_global_registry()
            return registry.get_quality_check(name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;QualityCheckPlugin | None&#x22;">
        QualityCheckPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_quality_provider&#x22;" type="&#x22;(name) -> QualityProviderPlugin | None&#x22;">
      Get a quality provider plugin by name.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        provider = get_quality_provider("pandera")
        if provider:
            decorator = provider.get_decorator()
            check_classes = provider.get_check_classes()
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_quality_provider(name: str) -> QualityProviderPlugin | None:
            """
            Get a quality provider plugin by name.

            Args:
                name: Plugin name (e.g., "pandera")

            Returns:
                QualityProviderPlugin instance or None if not found

            Example:
                \```python
                provider = get_quality_provider("pandera")
                if provider:
                    decorator = provider.get_decorator()
                    check_classes = provider.get_check_classes()
                \```
            """
            registry = get_global_registry()
            return registry.get_quality_provider(name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name (e.g., "pandera")
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;QualityProviderPlugin | None&#x22;">
        QualityProviderPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_ingestion_provider&#x22;" type="&#x22;(name) -> IngestionProviderPlugin | None&#x22;">
      Get an ingestion provider plugin by name.

      <PySourceCode>
        ```python
        def get_ingestion_provider(name: str) -> IngestionProviderPlugin | None:
            """
            Get an ingestion provider plugin by name.

            Args:
                name: Plugin name (e.g., "dlt")

            Returns:
                IngestionProviderPlugin instance or None if not found
            """
            registry = get_global_registry()
            return registry.get_ingestion_provider(name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name (e.g., "dlt")
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;IngestionProviderPlugin | None&#x22;">
        IngestionProviderPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_transformation_provider&#x22;" type="&#x22;(name) -> TransformationProviderPlugin | None&#x22;">
      Get a transformation provider plugin by name.

      <PySourceCode>
        ```python
        def get_transformation_provider(name: str) -> TransformationProviderPlugin | None:
            """
            Get a transformation provider plugin by name.

            Args:
                name: Plugin name (e.g., "dbt")

            Returns:
                TransformationProviderPlugin instance or None if not found
            """
            registry = get_global_registry()
            return registry.get_transformation_provider(name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name (e.g., "dbt")
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;TransformationProviderPlugin | None&#x22;">
        TransformationProviderPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_transformation&#x22;" type="&#x22;(name) -> TransformationPlugin | None&#x22;">
      Get a transformation plugin by name.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        pivot = get_transformation("pivot")
        if pivot:
            result = pivot.transform(df, config=\{"index": "date", ...\})
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_transformation(name: str) -> TransformationPlugin | None:
            """
            Get a transformation plugin by name.

            Args:
                name: Plugin name

            Returns:
                TransformationPlugin instance or None if not found

            Example:
                \```python
                pivot = get_transformation("pivot")
                if pivot:
                    result = pivot.transform(df, config={"index": "date", ...})
                \```
            """
            registry = get_global_registry()
            return registry.get_transformation(name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;TransformationPlugin | None&#x22;">
        TransformationPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_service&#x22;" type="&#x22;(name) -> ServicePlugin | None&#x22;">
      Get a service plugin by name.

      <PySourceCode>
        ```python
        def get_service(name: str) -> ServicePlugin | None:
            """
            Get a service plugin by name.

            Args:
                name: Plugin name

            Returns:
                ServicePlugin instance or None if not found
            """
            registry = get_global_registry()
            return registry.get_service(name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;ServicePlugin | None&#x22;">
        ServicePlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_hook_plugin&#x22;" type="&#x22;(name) -> HookPlugin | None&#x22;">
      Get a hook plugin by name.

      <PySourceCode>
        ```python
        def get_hook_plugin(name: str) -> HookPlugin | None:
            """
            Get a hook plugin by name.

            Args:
                name: Plugin name

            Returns:
                HookPlugin instance or None if not found
            """
            registry = get_global_registry()
            return registry.get_hook_plugin(name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;HookPlugin | None&#x22;">
        HookPlugin instance or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_plugin_info&#x22;" type="&#x22;(plugin_type, name) -> dict | None&#x22;">
      Get detailed information about a plugin.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        info = get_plugin_info("source_connectors", "github")
        if info:
            version = info["version"]
            author = info["author"]
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_plugin_info(plugin_type: str, name: str) -> dict | None:
            """
            Get detailed information about a plugin.

            Args:
                plugin_type: Plugin type ("source_connectors", "quality_checks", "transformations",
                    "services", "cli_commands", "hooks", "catalogs")
                name: Plugin name

            Returns:
                Dictionary with plugin information or None if not found

            Example:
                \```python
                info = get_plugin_info("source_connectors", "github")
                if info:
                    version = info["version"]
                    author = info["author"]
                \```
            """
            registry = get_global_registry()
            return registry.get_plugin_metadata(plugin_type, name)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin type ("source\_connectors", "quality\_checks", "transformations",
          "services", "cli\_commands", "hooks", "catalogs")
        </PyParameter>

        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Plugin name
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict | None&#x22;">
        Dictionary with plugin information or None if not found
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;validate_plugins&#x22;" type="&#x22;() -> dict[str, list[str]]&#x22;">
      Validate all registered plugins.

      Checks that all plugins comply with their interface requirements.

      <PySourceCode>
        ```python
        def validate_plugins() -> dict[str, list[str]]:
            """
            Validate all registered plugins.

            Checks that all plugins comply with their interface requirements.

            Returns:
                Dictionary with two keys:
                - 'valid': List of valid plugin names
                - 'invalid': List of invalid plugin names
            """
            registry = get_global_registry()
            all_plugins = registry.list_all_plugins()

            valid = []
            invalid = []

            for plugin_type, plugin_names in all_plugins.items():
                getter_method = _PLUGIN_GETTER_METHODS.get(plugin_type)
                if not getter_method:
                    continue
                getter = getattr(registry, getter_method)
                for name in plugin_names:
                    plugin = getter(name)
                    if plugin and registry.validate_plugin(plugin):
                        valid.append(f"{plugin_type}:{name}")
                    else:
                        invalid.append(f"{plugin_type}:{name}")

            return {"valid": valid, "invalid": invalid}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with two keys:
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;auto_discover&#x22;" type="&#x22;() -> None&#x22;">
      Automatically discover and register all plugins on import.

      This function is called automatically when phlo is imported.
      It discovers all installed plugins and registers them in the
      global registry.

      <PySourceCode>
        ```python
        def auto_discover() -> None:
            """
            Automatically discover and register all plugins on import.

            This function is called automatically when phlo is imported.
            It discovers all installed plugins and registers them in the
            global registry.
            """
            try:
                discover_plugins(auto_register=True)
            except Exception:
                logger.warning("plugin_auto_discover_failed", exc_info=True)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_is_auto_discover_disabled_by_env&#x22;" type="&#x22;() -> bool&#x22;">
      Return True when PHLO\_NO\_AUTO\_DISCOVER explicitly disables discovery.

      <PySourceCode>
        ```python
        def _is_auto_discover_disabled_by_env() -> bool:
            """Return True when PHLO_NO_AUTO_DISCOVER explicitly disables discovery."""
            return _is_auto_discover_disabled_by_env_impl()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_should_auto_discover&#x22;" type="&#x22;() -> bool&#x22;">
      Resolve auto-discovery using settings default plus env override precedence.

      <PySourceCode>
        ```python
        def _should_auto_discover() -> bool:
            """Resolve auto-discovery using settings default plus env override precedence."""
            return _should_auto_discover_impl()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
