# InMemorySettingsService (/docs/python-reference/core/phlo/plugins/observatory_settings/InMemorySettingsService)



In-memory fallback settings service for non-Postgres environments.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(self) -> None:
        self._store: dict[tuple[SettingsScope, str], SettingsRecord] = {}
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get&#x22;" type="&#x22;(self, scope, namespace) -> SettingsRecord | None&#x22;">
  <PySourceCode>
    ```python
    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        return self._store.get((scope, namespace))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;scope&#x22;" type="&#x22;SettingsScope&#x22;" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.observatory_settings.SettingsRecord | None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;put&#x22;" type="&#x22;(self, scope, namespace, settings, schema=None) -> SettingsRecord&#x22;">
  <PySourceCode>
    ```python
    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord:
        if schema:
            try:
                validate(instance=settings, schema=schema)
            except ValidationError as exc:
                raise ValueError(str(exc)) from exc
        record = SettingsRecord(
            scope=scope,
            namespace=namespace,
            settings=settings,
            updated_at=None,
        )
        self._store[(scope, namespace)] = record
        return record
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;scope&#x22;" type="&#x22;SettingsScope&#x22;" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;settings&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;phlo.plugins.observatory_settings.SettingsRecord&#x22;" />
</PyFunction>
