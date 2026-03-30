# OpenMetadataCatalogProvider (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/metadata_catalog/OpenMetadataCatalogProvider)



Capability provider for publishing metadata into OpenMetadata.

Wraps the OpenMetadataClient to provide a standardized interface
for the phlo capability system. Handles lazy client initialization
and configuration resolution.

Attributes [#attributes]

<PyAttribute name="&#x22;_client&#x22;" type="&#x22;OpenMetadataClient | None&#x22;" value="&#x22;None&#x22;">
  Cached OpenMetadataClient instance (initialized lazily).
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self) -> None&#x22;">
  Initialize with lazy client construction.

  The OpenMetadata client is created on first use to avoid
  unnecessary connections.

  <PySourceCode>
    ```python
    def __init__(self) -> None:
        """Initialize with lazy client construction.

        The OpenMetadata client is created on first use to avoid
        unnecessary connections.
        """
        self._client: OpenMetadataClient | None = None
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;health_check&#x22;" type="&#x22;(self) -> bool&#x22;">
  Check OpenMetadata connectivity.

  <PySourceCode>
    ```python
    def health_check(self) -> bool:
        """Check OpenMetadata connectivity.

        Returns:
            bool: True if OpenMetadata is reachable, False otherwise.

        """
        return self._get_client().health_check()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;">
    True if OpenMetadata is reachable, False otherwise.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;upsert_table&#x22;" type="&#x22;(self, *, namespace, table) -> Any&#x22;">
  Create or update a table entity in OpenMetadata.

  <PySourceCode>
    ```python
    def upsert_table(self, *, namespace: str, table: Any) -> Any:
        """Create or update a table entity in OpenMetadata.

        Args:
            namespace: Schema/namespace for the table.
            table: Table object (typically OpenMetadataTable).

        Returns:
            Any: Response from OpenMetadata API.

        """
        return self._get_client().create_or_update_table(schema_name=namespace, table=table)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
      Schema/namespace for the table.
    </PyParameter>

    <PyParameter name="&#x22;table&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Table object (typically OpenMetadataTable).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Response from OpenMetadata API.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_quality_result&#x22;" type="&#x22;(self, *, event) -> None&#x22;">
  Publish a quality result into OpenMetadata test metadata.

  Creates test definitions, test cases, and publishes results
  for quality checks.

  <PySourceCode>
    ```python
    def publish_quality_result(self, *, event: Any) -> None:
        """Publish a quality result into OpenMetadata test metadata.

        Creates test definitions, test cases, and publishes results
        for quality checks.

        Args:
            event: QualityResultEvent containing check results.

        Returns:
            None

        """
        if not isinstance(event, QualityResultEvent):
            return

        table_fqn = _resolve_table_fqn(event)
        if not table_fqn:
            return

        client = self._get_client()
        test_name = event.check_name
        client.create_test_definition(
            test_name=test_name,
            test_type=_resolve_test_type(event),
            entity_type=_resolve_entity_type(event),
        )
        test_case = client.create_test_case(
            test_case_name=f"{table_fqn}_{test_name}",
            table_fqn=table_fqn,
            test_definition_name=test_name,
        )
        test_case_fqn = (
            test_case.get("fullyQualifiedName")
            or test_case.get("name")
            or (f"{table_fqn}_{test_name}")
        )
        result_value = event.metadata.get("metric_value")
        client.publish_test_result(
            test_case_fqn=test_case_fqn,
            result="Success" if event.passed else "Failed",
            test_execution_date=datetime.now(timezone.utc),
            result_value=str(result_value) if result_value is not None else None,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;event&#x22;" type="&#x22;Any&#x22;" value="undefined">
      QualityResultEvent containing check results.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_lineage_edges&#x22;" type="&#x22;(self, *, edges) -> None&#x22;">
  Publish lineage edges into OpenMetadata.

  <PySourceCode>
    ```python
    def publish_lineage_edges(self, *, edges: list[tuple[str, str]]) -> None:
        """Publish lineage edges into OpenMetadata.

        Args:
            edges: List of (from_fqn, to_fqn) tuples representing lineage.

        Returns:
            None

        """
        client = self._get_client()
        for from_fqn, to_fqn in edges:
            client.create_lineage(from_fqn, to_fqn)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;edges&#x22;" type="&#x22;list[tuple[str, str]]&#x22;" value="undefined">
      List of (from\_fqn, to\_fqn) tuples representing lineage.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;">
    None
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_client&#x22;" type="&#x22;(self) -> OpenMetadataClient&#x22;">
  Return the lazily initialized OpenMetadata client.

  Creates the client on first call using configured settings.

  <PySourceCode>
    ```python
    def _get_client(self) -> OpenMetadataClient:
        """Return the lazily initialized OpenMetadata client.

        Creates the client on first call using configured settings.

        Returns:
            OpenMetadataClient: Client instance.

        """
        if self._client is None:
            settings = get_openmetadata_settings()
            self._client = OpenMetadataClient(
                base_url=settings.openmetadata_uri(),
                username=settings.openmetadata_username,
                password=settings.openmetadata_password,
                verify_ssl=settings.openmetadata_verify_ssl,
                service_name=settings.openmetadata_service_name,
                service_type=settings.openmetadata_database_service_type(),
                database_name=settings.openmetadata_database(),
            )
        return self._client
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;phlo_openmetadata.openmetadata.OpenMetadataClient&#x22;">
    Client instance.
  </PyFunctionReturn>
</PyFunction>
