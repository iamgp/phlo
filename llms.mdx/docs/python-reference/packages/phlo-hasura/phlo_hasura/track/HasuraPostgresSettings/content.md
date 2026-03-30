# HasuraPostgresSettings (/docs/python-reference/packages/phlo-hasura/phlo_hasura/track/HasuraPostgresSettings)



PostgreSQL connection settings used by Hasura table tracking.

Pydantic model for PostgreSQL connection configuration with sensible
defaults for Docker environments.

Attributes [#attributes]

<PyAttribute name="&#x22;postgres_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='postgres', description='PostgreSQL host')&#x22;">
  PostgreSQL server hostname (default: "postgres").
</PyAttribute>

<PyAttribute name="&#x22;postgres_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=5432, description='PostgreSQL port')&#x22;">
  PostgreSQL server port (default: 5432).
</PyAttribute>

<PyAttribute name="&#x22;postgres_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL username')&#x22;">
  Database username (default: "phlo").
</PyAttribute>

<PyAttribute name="&#x22;postgres_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL password')&#x22;">
  Database password (default: "phlo").
</PyAttribute>

<PyAttribute name="&#x22;postgres_db&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL database name')&#x22;">
  Database name (default: "phlo").
</PyAttribute>
