# LoggingSettings (/docs/python-reference/core/phlo/logging/LoggingSettings)



Configuration values for logging initialization.

Attributes [#attributes]

<PyAttribute name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="&#x22;'INFO'&#x22;" />

<PyAttribute name="&#x22;log_format&#x22;" type="&#x22;str&#x22;" value="&#x22;'auto'&#x22;" />

<PyAttribute name="&#x22;router_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />

<PyAttribute name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'phlo'&#x22;" />

<PyAttribute name="&#x22;log_file_template&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

<PyAttribute name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'dev'&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;from_settings&#x22;" type="&#x22;(cls) -> LoggingSettings&#x22;">
  Build logging settings from global application settings.

  <PySourceCode>
    ```python
    @classmethod
    def from_settings(cls) -> LoggingSettings:
        """Build logging settings from global application settings.

        Returns:
            LoggingSettings: Logging settings resolved from app configuration.

        """
        settings = get_settings()
        return cls(
            level=settings.phlo_log_level,
            log_format=settings.phlo_log_format,
            router_enabled=settings.phlo_log_router_enabled,
            service_name=settings.phlo_log_service_name,
            log_file_template=settings.phlo_log_file_template,
            environment=settings.phlo_environment,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.logging.LoggingSettings&#x22;">
    Logging settings resolved from app configuration.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, level='INFO', log_format='auto', router_enabled=True, service_name='phlo', log_file_template=None, environment='dev') -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="&#x22;'INFO'&#x22;" />

    <PyParameter name="&#x22;log_format&#x22;" type="&#x22;str&#x22;" value="&#x22;'auto'&#x22;" />

    <PyParameter name="&#x22;router_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="&#x22;'phlo'&#x22;" />

    <PyParameter name="&#x22;log_file_template&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;environment&#x22;" type="&#x22;str&#x22;" value="&#x22;'dev'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
