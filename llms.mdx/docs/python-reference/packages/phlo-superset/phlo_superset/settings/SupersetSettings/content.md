# SupersetSettings (/docs/python-reference/packages/phlo-superset/phlo_superset/settings/SupersetSettings)



Configuration settings for Apache Superset integration.

This class defines all configurable parameters for the Superset service
including network ports, authentication credentials, and administrative
settings. Values can be overridden via environment variables.

Attributes [#attributes]

<PyAttribute name="&#x22;superset_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10007, description='Superset web port')&#x22;">
  Port number for the Superset web UI (default: 10007).
</PyAttribute>

<PyAttribute name="&#x22;superset_admin_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='admin', description='Superset admin username')&#x22;">
  Username for the default admin account.
</PyAttribute>

<PyAttribute name="&#x22;superset_admin_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='admin', description='Superset admin password')&#x22;">
  Password for the default admin account.
</PyAttribute>

<PyAttribute name="&#x22;superset_admin_email&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='admin@example.com', description='Superset admin email')&#x22;">
  Email address for the default admin account.
</PyAttribute>
