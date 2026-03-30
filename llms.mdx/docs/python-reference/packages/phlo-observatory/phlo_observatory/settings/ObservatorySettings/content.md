# ObservatorySettings (/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings/ObservatorySettings)



Configuration settings for the Observatory UI.

Attributes [#attributes]

<PyAttribute name="&#x22;observatory_settings_db_url&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, validation_alias=(AliasChoices('PHLO_OBSERVATORY_SETTINGS_DB_URL')), description='PostgreSQL DSN for Observatory settings storage')&#x22;">
  PostgreSQL connection string for persisting
  Observatory settings. If not provided, settings are stored in-memory.
</PyAttribute>
