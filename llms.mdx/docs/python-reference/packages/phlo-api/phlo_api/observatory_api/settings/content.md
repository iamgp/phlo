# settings (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/settings)



Server-wide Observatory settings endpoints.

Provides CRUD operations for global Observatory configuration.
Settings are persisted via the settings service and validated
against a strict JSON schema to ensure UI compatibility.

Key Endpoints:
GET /api/observatory/settings: Get global Observatory settings.
PUT /api/observatory/settings: Update global Observatory settings.

Example:
Getting settings:

.. code-block:: bash

curl [http://localhost:4000/api/observatory/settings](http://localhost:4000/api/observatory/settings)

Response includes connections, defaults, query, and UI configuration.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(prefix='/api/observatory', tags=['observatory'])&#x22;" />

<PyAttribute name="&#x22;OBSERVATORY_SETTINGS_SCHEMA&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;{'type': 'object', 'additionalProperties': False, 'required': ['version', 'connections', 'defaults', 'query', 'ui'], 'properties': {'version': {'type': 'integer', 'enum': [1]}, 'connections': {'type': 'object', 'additionalProperties': False, 'required': ['dagsterGraphqlUrl', 'trinoUrl', 'nessieUrl'], 'properties': {'dagsterGraphqlUrl': {'type': 'string', 'minLength': 1}, 'trinoUrl': {'type': 'string', 'minLength': 1}, 'nessieUrl': {'type': 'string', 'minLength': 1}}}, 'defaults': {'type': 'object', 'additionalProperties': False, 'required': ['branch', 'catalog', 'schema'], 'properties': {'branch': {'type': 'string', 'minLength': 1}, 'catalog': {'type': 'string', 'minLength': 1}, 'schema': {'type': 'string', 'minLength': 1}}}, 'query': {'type': 'object', 'additionalProperties': False, 'required': ['readOnlyMode', 'defaultLimit', 'maxLimit', 'timeoutMs'], 'properties': {'readOnlyMode': {'type': 'boolean'}, 'defaultLimit': {'type': 'integer', 'minimum': 1, 'maximum': 100000}, 'maxLimit': {'type': 'integer', 'minimum': 1, 'maximum': 100000}, 'timeoutMs': {'type': 'integer', 'minimum': 1000, 'maximum': 300000}}}, 'ui': {'type': 'object', 'additionalProperties': False, 'required': ['density', 'dateFormat'], 'properties': {'density': {'type': 'string', 'enum': ['comfortable', 'compact']}, 'dateFormat': {'type': 'string', 'enum': ['iso', 'local']}}}, 'auth': {'type': 'object', 'additionalProperties': False, 'properties': {'token': {'type': 'string'}}}, 'realtime': {'type': 'object', 'additionalProperties': False, 'required': ['enabled', 'intervalMs'], 'properties': {'enabled': {'type': 'boolean'}, 'intervalMs': {'type': 'integer', 'minimum': 1000, 'maximum': 60000}}}}}&#x22;" />

<PyAttribute name="&#x22;OBSERVATORY_SETTINGS_NAMESPACE&#x22;" type="null" value="&#x22;'observatory.core'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ObservatorySettingsPayload&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/settings/ObservatorySettingsPayload&#x22;" />

      <Card title="&#x22;ObservatorySettingsResponse&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/settings/ObservatorySettingsResponse&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_fetch_settings_sync&#x22;" type="&#x22;() -> ObservatorySettingsResponse&#x22;">
      Fetch persisted global Observatory settings.

      <PySourceCode>
        ```python
        def _fetch_settings_sync() -> ObservatorySettingsResponse:
            """Fetch persisted global Observatory settings.

            Returns:
                ObservatorySettingsResponse: Stored settings and update timestamp.

            """
            service = get_settings_service()
            record = service.get(SettingsScope.GLOBAL, OBSERVATORY_SETTINGS_NAMESPACE)
            if not record:
                return ObservatorySettingsResponse(settings=None, updated_at=None)
            return ObservatorySettingsResponse(
                settings=record.settings,
                updated_at=record.updated_at,
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.settings.ObservatorySettingsResponse&#x22;">
        Stored settings and update timestamp.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_upsert_settings_sync&#x22;" type="&#x22;(payload) -> ObservatorySettingsResponse&#x22;">
      Persist global Observatory settings.

      <PySourceCode>
        ```python
        def _upsert_settings_sync(payload: ObservatorySettingsPayload) -> ObservatorySettingsResponse:
            """Persist global Observatory settings.

            Args:
                payload: Incoming settings payload.

            Returns:
                ObservatorySettingsResponse: Saved settings and update timestamp.

            """
            service = get_settings_service()
            record = service.put(
                SettingsScope.GLOBAL,
                OBSERVATORY_SETTINGS_NAMESPACE,
                payload.settings,
                schema=OBSERVATORY_SETTINGS_SCHEMA,
            )
            return ObservatorySettingsResponse(
                settings=record.settings,
                updated_at=record.updated_at,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;ObservatorySettingsPayload&#x22;" value="undefined">
          Incoming settings payload.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.settings.ObservatorySettingsResponse&#x22;">
        Saved settings and update timestamp.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_observatory_settings&#x22;" type="&#x22;(request) -> ObservatorySettingsResponse&#x22;">
      Fetch server-wide Observatory settings.

      <PySourceCode>
        ```python
        @router.get("/settings", response_model=ObservatorySettingsResponse)
        async def get_observatory_settings(request: Request) -> ObservatorySettingsResponse:
            """Fetch server-wide Observatory settings.

            Args:
                request: FastAPI request object for authorization checks.

            Returns:
                ObservatorySettingsResponse with current settings and update timestamp.

            Raises:
                HTTPException: If settings service is unavailable (503) or on other errors (500).

            """
            check_admin_read(request, "observatory_settings")
            try:
                return await run_sync(_fetch_settings_sync)
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            except Exception as exc:
                logger.exception("Failed to fetch Observatory settings")
                raise HTTPException(status_code=500, detail="Failed to fetch settings") from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          FastAPI request object for authorization checks.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.settings.ObservatorySettingsResponse&#x22;">
        ObservatorySettingsResponse with current settings and update timestamp.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;put_observatory_settings&#x22;" type="&#x22;(request, payload) -> ObservatorySettingsResponse&#x22;">
      Replace server-wide Observatory settings.

      <PySourceCode>
        ```python
        @router.put("/settings", response_model=ObservatorySettingsResponse)
        async def put_observatory_settings(
            request: Request,
            payload: ObservatorySettingsPayload,
        ) -> ObservatorySettingsResponse:
            """Replace server-wide Observatory settings.

            Args:
                request: FastAPI request object for authorization checks.
                payload: ObservatorySettingsPayload with new settings values.

            Returns:
                ObservatorySettingsResponse with saved settings and update timestamp.

            Raises:
                HTTPException: If settings service is unavailable (503), validation fails (422),
                    or on other errors (500).

            """
            check_admin_manage(request, "observatory_settings")
            try:
                return await run_sync(_upsert_settings_sync, payload)
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            except Exception as exc:
                logger.exception("Failed to update Observatory settings")
                raise HTTPException(status_code=500, detail="Failed to update settings") from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;request&#x22;" type="&#x22;Request&#x22;" value="undefined">
          FastAPI request object for authorization checks.
        </PyParameter>

        <PyParameter name="&#x22;payload&#x22;" type="&#x22;ObservatorySettingsPayload&#x22;" value="undefined">
          ObservatorySettingsPayload with new settings values.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.observatory_api.settings.ObservatorySettingsResponse&#x22;">
        ObservatorySettingsResponse with saved settings and update timestamp.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
