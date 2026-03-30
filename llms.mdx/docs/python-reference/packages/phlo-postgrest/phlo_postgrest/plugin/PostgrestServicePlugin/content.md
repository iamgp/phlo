# PostgrestServicePlugin (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/plugin/PostgrestServicePlugin)



Service plugin for managing PostgREST container lifecycle.

This plugin integrates PostgREST with Phlo's service management system,
providing Docker Compose configuration and metadata for the REST API
service automatically generated from PostgreSQL schemas.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin identification and version info.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Docker Compose service configuration.
</PyAttribute>
