# SettingsService (/docs/python-reference/core/phlo/plugins/observatory_settings/SettingsService)



Settings service with optional schema validation.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, db_url) -> None&#x22;">
  <PySourceCode>
    ```python
    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._table_ensured = False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;db_url&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get&#x22;" type="&#x22;(self, scope, namespace) -> SettingsRecord | None&#x22;">
  Get settings for a scope and namespace.

  <PySourceCode>
    ```python
    def get(self, scope: SettingsScope, namespace: str) -> SettingsRecord | None:
        """Get settings for a scope and namespace."""
        with psycopg2.connect(self._db_url) as conn:
            self._ensure_table(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT settings, updated_at
                    FROM phlo_settings
                    WHERE scope = %s AND namespace = %s
                    """,
                    (scope.value, namespace),
                )
                row = cursor.fetchone()
                if not row:
                    logger.debug(
                        "observatory_settings_not_found",
                        scope=scope.value,
                        namespace=namespace,
                    )
                    return None
                settings, updated_at = row
                return SettingsRecord(
                    scope=scope,
                    namespace=namespace,
                    settings=settings,
                    updated_at=updated_at.isoformat() if updated_at else None,
                )
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
  Upsert settings for a scope and namespace.

  <PySourceCode>
    ```python
    def put(
        self,
        scope: SettingsScope,
        namespace: str,
        settings: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> SettingsRecord:
        """Upsert settings for a scope and namespace."""
        self._validate(settings, schema)
        with psycopg2.connect(self._db_url) as conn:
            self._ensure_table(conn)
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO phlo_settings (scope, namespace, settings, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (scope, namespace)
                    DO UPDATE SET settings = EXCLUDED.settings, updated_at = NOW()
                    RETURNING settings, updated_at
                    """,
                    (scope.value, namespace, settings),
                )
                stored_settings, updated_at = cursor.fetchone()
                conn.commit()
                return SettingsRecord(
                    scope=scope,
                    namespace=namespace,
                    settings=stored_settings,
                    updated_at=updated_at.isoformat() if updated_at else None,
                )
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

<PyFunction name="&#x22;_validate&#x22;" type="&#x22;(self, settings, schema) -> None&#x22;">
  <PySourceCode>
    ```python
    def _validate(self, settings: dict[str, Any], schema: dict[str, Any] | None) -> None:
        if not schema:
            return
        try:
            validate(instance=settings, schema=schema)
        except ValidationError as exc:
            logger.warning("observatory_settings_validation_failed", error=str(exc))
            raise ValueError(str(exc)) from exc
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;settings&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_ensure_table&#x22;" type="&#x22;(self, conn) -> None&#x22;">
  <PySourceCode>
    ```python
    def _ensure_table(self, conn) -> None:
        if self._table_ensured:
            return
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS phlo_settings (
                    scope TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    settings JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (scope, namespace)
                )
                """
            )
            conn.commit()
        self._table_ensured = True
        logger.debug("observatory_settings_table_ensured")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;conn&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
