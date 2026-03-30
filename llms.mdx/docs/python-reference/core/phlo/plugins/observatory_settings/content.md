# observatory_settings (/docs/python-reference/core/phlo/plugins/observatory_settings)



Core settings storage contracts and helpers for Observatory backends.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ObservatorySettingsStorageConfig&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings/ObservatorySettingsStorageConfig&#x22;" />

      <Card title="&#x22;SettingsScope&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings/SettingsScope&#x22;" />

      <Card title="&#x22;SettingsRecord&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings/SettingsRecord&#x22;" />

      <Card title="&#x22;SettingsService&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings/SettingsService&#x22;" />

      <Card title="&#x22;InMemorySettingsService&#x22;" href="&#x22;/docs/python-reference/core/phlo/plugins/observatory_settings/InMemorySettingsService&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings_service&#x22;" type="&#x22;() -> SettingsService | InMemorySettingsService&#x22;">
      Build and cache the settings service instance.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings_service() -> SettingsService | InMemorySettingsService:
            """Build and cache the settings service instance."""
            config = ObservatorySettingsStorageConfig()
            if config.observatory_settings_db_url:
                logger.debug("observatory_settings_service_initialized", backend="postgres_explicit")
                return SettingsService(config.observatory_settings_db_url)

            try:
                from phlo_postgres.settings import get_settings as get_postgres_settings
            except Exception:
                logger.warning("observatory_settings_falling_back_to_memory")
                return InMemorySettingsService()

            postgres_settings = get_postgres_settings()
            db_url = postgres_settings.get_postgres_connection_string()
            logger.debug("observatory_settings_service_initialized", backend="postgres_default")
            return SettingsService(db_url)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.plugins.observatory_settings.SettingsService | phlo.plugins.observatory_settings.InMemorySettingsService&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
