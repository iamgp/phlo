# LineageSettings (/docs/python-reference/packages/phlo-lineage/phlo_lineage/settings/LineageSettings)



Configuration settings for the lineage store and related features.

This Pydantic model defines all configuration options for phlo-lineage,
with automatic environment variable loading and validation.

Attributes [#attributes]

<PyAttribute name="&#x22;lineage_db_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, validation_alias=(AliasChoices('LINEAGE_DB_URL', 'PHLO_LINEAGE_DB_URL', 'DAGSTER_PG_DB_CONNECTION_STRING')), description='PostgreSQL DSN for the row-level lineage store')&#x22;">
  PostgreSQL connection string for the lineage database.
  Supports multiple environment variable aliases for flexibility
  across different deployment scenarios.
</PyAttribute>
