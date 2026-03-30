# discovery (/docs/python-reference/core/phlo/capabilities/discovery)



Capability discovery for asset and resource providers.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;discover_capabilities&#x22;" type="&#x22;() -> None&#x22;">
      Discover capability providers and register their specs.

      <PySourceCode>
        ```python
        def discover_capabilities() -> None:
            """Discover capability providers and register their specs."""
            logger.info("capability_discovery_started")
            register_default_capability_providers()
            discover_plugins(plugin_type="asset_providers", auto_register=True)
            discover_plugins(plugin_type="resource_providers", auto_register=True)

            registry = get_global_registry()

            asset_provider_count = 0
            for name in registry.list_asset_providers():
                plugin = registry.get_asset_provider(name)
                if plugin is None:
                    continue
                asset_provider_count += 1
                try:
                    for asset in plugin.get_assets():
                        register_asset(asset)
                    for check in plugin.get_checks():
                        register_check(check)
                except Exception as exc:
                    logger.warning(
                        "capability_asset_provider_registration_failed",
                        provider_name=name,
                        error=str(exc),
                        exc_info=True,
                    )

            resource_provider_count = 0
            for name in registry.list_resource_providers():
                plugin = registry.get_resource_provider(name)
                if plugin is None:
                    continue
                resource_provider_count += 1
                try:
                    for resource in plugin.get_resources():
                        register_resource(resource)
                    for table_store in plugin.get_table_stores():
                        register_table_store(table_store)
                    for catalog in plugin.get_catalogs():
                        register_catalog(catalog)
                    for catalog_scanner in plugin.get_catalog_scanners():
                        register_catalog_scanner(catalog_scanner)
                    for query_engine in plugin.get_query_engines():
                        register_query_engine(query_engine)
                    for object_store in plugin.get_object_stores():
                        register_object_store(object_store)
                    for quality_backend in plugin.get_quality_backends():
                        register_quality_backend(quality_backend)
                    for maintenance_read_model in plugin.get_maintenance_read_models():
                        register_maintenance_read_model(maintenance_read_model)
                    for metadata_catalog in plugin.get_metadata_catalogs():
                        register_metadata_catalog(metadata_catalog)
                    for lineage_sink in plugin.get_lineage_sinks():
                        register_lineage_sink(lineage_sink)
                    for governance_backend in plugin.get_governance_backends():
                        register_governance_backend(governance_backend)
                    for authorization_policy_backend in plugin.get_authorization_policy_backends():
                        register_authorization_policy_backend(authorization_policy_backend)
                    for authentication_provider in plugin.get_authentication_providers():
                        register_authentication_provider(authentication_provider)
                    for publish_target in plugin.get_publish_targets():
                        register_publish_target(publish_target)
                    for alert_sink in plugin.get_alert_sinks():
                        register_alert_sink(alert_sink)
                    for api_backend in plugin.get_api_backends():
                        register_api_backend(api_backend)
                    for secret_backend in plugin.get_secret_backends():
                        register_secret_backend(secret_backend)
                    for schema_migrator in plugin.get_schema_migrators():
                        register_schema_migrator(schema_migrator)
                    for source_adapter in plugin.get_data_migration_sources():
                        register_data_migration_source(source_adapter)
                    for observability_backend in plugin.get_observability_backends():
                        register_observability_backend(observability_backend)
                except Exception as exc:
                    logger.warning(
                        "capability_resource_provider_registration_failed",
                        provider_name=name,
                        error=str(exc),
                        exc_info=True,
                    )

            logger.info(
                "capability_discovery_completed",
                asset_provider_count=asset_provider_count,
                resource_provider_count=resource_provider_count,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
