# PostgrestViewsSettings (/docs/python-reference/packages/phlo-postgrest/phlo_postgrest/views/PostgrestViewsSettings)



Configuration settings for PostgREST view generation.

Pydantic-based configuration class that loads settings from environment
variables and configuration files. Controls paths, database connections,
and schema selection for view generation.

Attributes [#attributes]

<PyAttribute name="&#x22;dbt_manifest_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='workflows/transforms/dbt/target/manifest.json', description='Path to dbt manifest.json')&#x22;">
  Path to dbt's manifest.json output.
</PyAttribute>

<PyAttribute name="&#x22;dbt_api_source_schema&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='dbt schema to expose through generated PostgREST views')&#x22;">
  Source schema to expose via PostgREST.
</PyAttribute>

<PyAttribute name="&#x22;postgres_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='postgres', description='PostgreSQL host')&#x22;">
  PostgreSQL server hostname.
</PyAttribute>

<PyAttribute name="&#x22;postgres_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=5432, description='PostgreSQL port')&#x22;">
  PostgreSQL server port.
</PyAttribute>

<PyAttribute name="&#x22;postgres_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL username')&#x22;">
  Database username.
</PyAttribute>

<PyAttribute name="&#x22;postgres_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL password')&#x22;">
  Database password.
</PyAttribute>

<PyAttribute name="&#x22;postgres_db&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL database name')&#x22;">
  Database name.
</PyAttribute>
