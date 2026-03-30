# SlingSettings (/docs/python-reference/packages/phlo-sling/phlo_sling/settings/SlingSettings)



Configuration for Sling replication defaults.

This class defines the configuration schema and defaults for Sling
replication operations within the Phlo platform. Settings are loaded
from environment variables prefixed appropriately and validated
using Pydantic.

Attributes [#attributes]

<PyAttribute name="&#x22;sling_default_namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='raw', description='Default namespace for generated replication table names.')&#x22;">
  Default namespace/prefix for generated
  replication table names. Tables will be created as
  `\{namespace\}.\{table_name\}`.
</PyAttribute>

<PyAttribute name="&#x22;sling_binary_path&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Override path to the sling binary. None uses the bundled binary.')&#x22;">
  Override path to the Sling binary executable.
  If None, the bundled binary from the sling package is used.
</PyAttribute>

<PyAttribute name="&#x22;sling_default_mode&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='incremental', description='Default replication mode (full-refresh, incremental, snapshot, backfill).')&#x22;">
  Default replication mode for Sling operations.
  Valid modes are "full-refresh", "incremental", "snapshot",
  and "backfill".
</PyAttribute>

<PyAttribute name="&#x22;sling_auto_connections&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Auto-generate Sling connections from Phlo capability metadata.')&#x22;">
  Whether to automatically generate Sling
  connection definitions from Phlo capability metadata.
</PyAttribute>

<PyAttribute name="&#x22;sling_connections_dir&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Directory containing Sling env.yaml files for explicit connections.')&#x22;">
  Directory path containing Sling env.yaml
  files for explicit connection definitions. If provided,
  these connections are merged with auto-discovered ones.
</PyAttribute>
