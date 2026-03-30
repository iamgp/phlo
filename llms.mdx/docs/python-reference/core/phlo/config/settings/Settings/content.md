# Settings (/docs/python-reference/core/phlo/config/settings/Settings)



Core configuration for Phlo.

This class defines all configurable aspects of the Phlo framework including
logging, orchestration, plugin management, and observability settings.
Values are loaded from environment variables with sensible defaults.

Environment variables are read with case-insensitive matching. Aliases
are provided for common configuration patterns (e.g., OTEL\_\* variables).

Attributes [#attributes]

<PyAttribute name="&#x22;phlo_orchestrator&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='dagster', validation_alias=(AliasChoices('PHLO_ORCHESTRATOR', 'PHLO_ORCHESTRATOR_NAME')), description='Active orchestrator adapter name')&#x22;">
  Active orchestrator adapter name (default: "dagster").
</PyAttribute>

<PyAttribute name="&#x22;phlo_log_level&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='INFO', description='Default log level for Phlo')&#x22;">
  Default log level (default: "INFO").
</PyAttribute>

<PyAttribute name="&#x22;phlo_log_format&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='auto', description='Log format (auto|json|console)')&#x22;">
  Log output format - "auto", "json", or "console".
</PyAttribute>

<PyAttribute name="&#x22;phlo_log_router_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Emit structured log events to the hook bus')&#x22;">
  Enable structured log event routing to hook bus.
</PyAttribute>

<PyAttribute name="&#x22;phlo_log_service_name&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='Default service name for log records')&#x22;">
  Default service name for log records.
</PyAttribute>

<PyAttribute name="&#x22;phlo_log_file_template&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='.phlo/logs/{YMD}.log', description='Optional log file path template (empty to disable)')&#x22;">
  Optional log file path template with date placeholders.
</PyAttribute>

<PyAttribute name="&#x22;phlo_environment&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='dev', validation_alias=(AliasChoices('PHLO_ENVIRONMENT', 'ENVIRONMENT')), description='Runtime environment attached to structured logs')&#x22;">
  Runtime environment identifier (dev, staging, prod).
</PyAttribute>

<PyAttribute name="&#x22;phlo_service_namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', validation_alias=(AliasChoices('PHLO_SERVICE_NAMESPACE', 'OTEL_SERVICE_NAMESPACE')), description='Default service namespace attached to observability resources')&#x22;">
  Service namespace for observability resources.
</PyAttribute>

<PyAttribute name="&#x22;phlo_service_version&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, validation_alias=(AliasChoices('PHLO_SERVICE_VERSION', 'OTEL_SERVICE_VERSION')), description='Optional default service version attached to observability resources')&#x22;">
  Optional service version for observability.
</PyAttribute>

<PyAttribute name="&#x22;phlo_service_instance_id&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, validation_alias=(AliasChoices('PHLO_SERVICE_INSTANCE_ID', 'OTEL_SERVICE_INSTANCE_ID')), description='Optional default service instance identifier for observability resources')&#x22;">
  Optional instance identifier for observability.
</PyAttribute>

<PyAttribute name="&#x22;phlo_project&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, validation_alias=(AliasChoices('PHLO_PROJECT')), description='Optional project identifier attached to observability resources')&#x22;">
  Optional project identifier for observability.
</PyAttribute>

<PyAttribute name="&#x22;phlo_default_capabilities&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;Field(default_factory=dict, validation_alias=(AliasChoices('PHLO_DEFAULT_CAPABILITIES')), description=\&#x22;Default capability provider names keyed by capability type (for example {'table_store': 'iceberg'})\&#x22;)&#x22;">
  Default capability provider mappings.
</PyAttribute>

<PyAttribute name="&#x22;plugins_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Enable plugin system')&#x22;">
  Enable the plugin system.
</PyAttribute>

<PyAttribute name="&#x22;plugins_auto_discover&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Automatically discover plugins from entry points on import')&#x22;">
  Automatically discover plugins from entry points.
</PyAttribute>

<PyAttribute name="&#x22;plugins_whitelist&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;Field(default_factory=list, description='Whitelist of plugin names to load (empty = all allowed)')&#x22;">
  List of allowed plugin names (empty = all allowed).
</PyAttribute>

<PyAttribute name="&#x22;plugins_blacklist&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;Field(default_factory=list, description='Blacklist of plugin names to exclude')&#x22;">
  List of plugin names to exclude.
</PyAttribute>

<PyAttribute name="&#x22;plugin_registry_url&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='https://registry.phlohouse.com/plugins.json', description='URL for the plugin registry catalog')&#x22;">
  URL for the plugin registry catalog.
</PyAttribute>

<PyAttribute name="&#x22;plugin_registry_cache_ttl_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=3600, description='Registry cache TTL in seconds')&#x22;">
  Cache TTL for registry responses.
</PyAttribute>

<PyAttribute name="&#x22;plugin_registry_timeout_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10, description='Registry fetch timeout in seconds')&#x22;">
  Timeout for registry fetch requests.
</PyAttribute>
