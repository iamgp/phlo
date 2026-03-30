# OpenMetadataHookPlugin (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/hooks_plugin/OpenMetadataHookPlugin)



Hook plugin that syncs lineage, quality, and publish events.

Automatically captures pipeline events and syncs them to OpenMetadata:

* Lineage edges between assets
* Quality check results as test cases
* Published table metadata

The plugin initializes the OpenMetadata client lazily and only syncs
when openmetadata\_sync\_enabled is True in settings.

Attributes [#attributes]

<PyAttribute name="&#x22;_client&#x22;" type="&#x22;OpenMetadataClient | None&#x22;" value="&#x22;None&#x22;">
  Cached OpenMetadataClient instance (initialized lazily).
</PyAttribute>

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Metadata for the OpenMetadata hook plugin.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize the plugin with lazy client setup.

  The OpenMetadata client is not created until first use to avoid
  connection overhead if sync is disabled.

  <PySourceCode>
    ```python
    def __init__(self) -> None:
        """Initialize the plugin with lazy client setup.

        The OpenMetadata client is not created until first use to avoid
        connection overhead if sync is disabled.
        """
        self._client: OpenMetadataClient | None = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_hooks&#x22;" type="&#x22;(self) -> list[HookRegistration]&#x22;">
  Register lineage, quality, and publish hook handlers.

  <PySourceCode>
    ```python
    def get_hooks(self) -> list[HookRegistration]:
        """Register lineage, quality, and publish hook handlers.

        Returns:
            list[HookRegistration]: List of HookRegistration objects for each
                supported event type.

        """
        return [
            HookRegistration(
                hook_name="openmetadata_lineage",
                handler=self._handle_lineage,
                filters=HookFilter(event_types={"lineage.edges"}),
            ),
            HookRegistration(
                hook_name="openmetadata_quality",
                handler=self._handle_quality_result,
                filters=HookFilter(event_types={"quality.result"}),
            ),
            HookRegistration(
                hook_name="openmetadata_publish",
                handler=self._handle_publish,
                filters=HookFilter(event_types={"publish.end"}),
            ),
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[HookRegistration]: List of HookRegistration objects for each
    supported event type.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;cleanup&#x22;" type="&#x22;(self) -> None&#x22;">
  Close the OpenMetadata client if initialized.

  Should be called during plugin shutdown to release resources.

  <PySourceCode>
    ```python
    def cleanup(self) -> None:
        """Close the OpenMetadata client if initialized.

        Should be called during plugin shutdown to release resources.

        Returns:
            None

        """
        if self._client:
            self._client.close()
            self._client = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_lineage&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Sync lineage edges into OpenMetadata.

  <PySourceCode>
    ```python
    def _handle_lineage(self, event: Any) -> None:
        """Sync lineage edges into OpenMetadata.

        Args:
            event: LineageEvent containing edges to sync.

        Returns:
            None

        """
        if not isinstance(event, LineageEvent):
            return
        logger.info("openmetadata_lineage_sync_started", edge_count=len(event.edges))
        client = self._get_client()
        if client is None:
            logger.info(
                "openmetadata_lineage_sync_result",
                edge_count=len(event.edges),
                synced_count=0,
                failed_count=0,
                skipped=True,
            )
            return
        synced_count = 0
        failed_count = 0
        for from_fqn, to_fqn in event.edges:
            try:
                client.create_lineage(from_fqn, to_fqn)
                synced_count += 1
            except Exception as exc:
                failed_count += 1
                logger.warning(
                    "openmetadata_lineage_sync_failed",
                    from_fqn=from_fqn,
                    to_fqn=to_fqn,
                    error=str(exc),
                )
        logger.info(
            "openmetadata_lineage_sync_result",
            edge_count=len(event.edges),
            synced_count=synced_count,
            failed_count=failed_count,
            skipped=False,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      LineageEvent containing edges to sync.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_quality_result&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Sync quality results into OpenMetadata test metadata.

  Creates or updates test definitions, test cases, and publishes
  test results for quality checks.

  <PySourceCode>
    ```python
    def _handle_quality_result(self, event: Any) -> None:
        """Sync quality results into OpenMetadata test metadata.

        Creates or updates test definitions, test cases, and publishes
        test results for quality checks.

        Args:
            event: QualityResultEvent with check results.

        Returns:
            None

        """
        if not isinstance(event, QualityResultEvent):
            return
        logger.info(
            "openmetadata_quality_sync_started",
            check_name=event.check_name,
            check_type=event.check_type,
            passed=event.passed,
        )
        client = self._get_client()
        if client is None:
            logger.info(
                "openmetadata_quality_sync_result",
                check_name=event.check_name,
                table_fqn=None,
                definition_synced=False,
                test_case_synced=False,
                test_result_published=False,
                failed_count=0,
                skipped=True,
            )
            return

        table_fqn = _resolve_table_fqn(event)
        if not table_fqn:
            logger.warning("openmetadata_quality_sync_skipped", reason="missing_table_fqn")
            logger.info(
                "openmetadata_quality_sync_result",
                check_name=event.check_name,
                table_fqn=None,
                definition_synced=False,
                test_case_synced=False,
                test_result_published=False,
                failed_count=0,
                skipped=True,
            )
            return

        test_name = event.check_name
        test_type = _resolve_test_type(event)
        entity_type = _resolve_entity_type(event)
        definition_synced = False
        test_case_synced = False
        test_result_published = False
        failed_count = 0
        try:
            client.create_test_definition(
                test_name=test_name, test_type=test_type, entity_type=entity_type
            )
            definition_synced = True
        except Exception as exc:
            failed_count += 1
            logger.warning(
                "openmetadata_quality_definition_sync_failed",
                check_name=test_name,
                table_fqn=table_fqn,
                error=str(exc),
            )

        test_case_name = f"{table_fqn}_{test_name}"
        test_case_fqn = test_case_name
        try:
            test_case = client.create_test_case(
                test_case_name=test_case_name,
                table_fqn=table_fqn,
                test_definition_name=test_name,
            )
            test_case_fqn = (
                test_case.get("fullyQualifiedName") or test_case.get("name") or test_case_name
            )
            test_case_synced = True
        except Exception as exc:
            failed_count += 1
            logger.warning(
                "openmetadata_quality_test_case_sync_failed",
                check_name=test_name,
                table_fqn=table_fqn,
                error=str(exc),
            )

        result_value = event.metadata.get("metric_value")
        try:
            client.publish_test_result(
                test_case_fqn=test_case_fqn,
                result="Success" if event.passed else "Failed",
                test_execution_date=datetime.now(timezone.utc),
                result_value=str(result_value) if result_value is not None else None,
            )
            test_result_published = True
        except Exception as exc:
            failed_count += 1
            logger.warning(
                "openmetadata_quality_test_result_publish_failed",
                check_name=test_name,
                table_fqn=table_fqn,
                error=str(exc),
            )

        logger.info(
            "openmetadata_quality_sync_result",
            check_name=event.check_name,
            table_fqn=table_fqn,
            definition_synced=definition_synced,
            test_case_synced=test_case_synced,
            test_result_published=test_result_published,
            failed_count=failed_count,
            skipped=False,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      QualityResultEvent with check results.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_handle_publish&#x22;" type="&#x22;(self, event) -> None&#x22;">
  Sync published tables into OpenMetadata.

  <PySourceCode>
    ```python
    def _handle_publish(self, event: Any) -> None:
        """Sync published tables into OpenMetadata.

        Args:
            event: PublishEvent with published table information.

        Returns:
            None

        """
        if not isinstance(event, PublishEvent):
            return
        if event.status != "success":
            return
        client = self._get_client()
        if client is None:
            return

        for target_table, target_fqn in event.tables.items():
            schema_name, table_name = _split_table_fqn(
                target_fqn,
                default_schema=os.getenv("PHLO_POSTGRES_MART_SCHEMA", "marts"),
            )
            try:
                table = OpenMetadataTable(name=table_name)
                client.create_or_update_table(schema_name=schema_name, table=table)
            except Exception as exc:
                logger.warning(
                    "OpenMetadata publish sync failed for %s: %s",
                    target_table,
                    exc,
                )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      PublishEvent with published table information.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_client&#x22;" type="&#x22;(self) -> OpenMetadataClient | None&#x22;">
  Return the OpenMetadata client if sync is enabled.

  Lazily initializes the client on first call. Returns None if
  sync is disabled in settings.

  <PySourceCode>
    ```python
    def _get_client(self) -> OpenMetadataClient | None:
        """Return the OpenMetadata client if sync is enabled.

        Lazily initializes the client on first call. Returns None if
        sync is disabled in settings.

        Returns:
            OpenMetadataClient | None: Client if enabled and configured,
                otherwise None.

        """
        settings = get_openmetadata_settings()
        if not settings.openmetadata_sync_enabled:
            return None
        if self._client is None:
            try:
                self._client = OpenMetadataClient(
                    base_url=settings.openmetadata_uri(),
                    username=settings.openmetadata_username,
                    password=settings.openmetadata_password,
                    verify_ssl=settings.openmetadata_verify_ssl,
                    service_name=settings.openmetadata_service_name,
                    service_type=settings.openmetadata_database_service_type(),
                    database_name=settings.openmetadata_database(),
                )
            except RuntimeError as exc:
                logger.warning("openmetadata_client_configuration_unavailable", error=str(exc))
                return None
        return self._client
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;OpenMetadataClient | None&#x22;">
    OpenMetadataClient | None: Client if enabled and configured,
    otherwise None.
  </PyFunctionReturn>
</PyFunction>
