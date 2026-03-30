# DltSettings (/docs/python-reference/packages/phlo-dlt/phlo_dlt/settings/DltSettings)



Configuration for DLT ingestion defaults.

Pydantic-based settings class that provides default configuration
values for DLT ingestion operations. Values can be overridden via
environment variables or .env files.

Attributes [#attributes]

<PyAttribute name="&#x22;dlt_default_namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='raw', description='Default namespace/schema used for generated ingestion table names.')&#x22;">
  Default namespace/schema used for generated
  ingestion table names. Prepended to table\_name to create
  full\_table\_name.
</PyAttribute>
