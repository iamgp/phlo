# plugin (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin)



ClickHouse service and resource provider plugins.

This module provides Phlo plugin implementations for ClickHouse integration,
including service management, resource provisioning, and capability discovery.

Example:
Using the ClickHouse plugins:

> > > from phlo\_clickhouse.plugin import ClickHouseServicePlugin
> > > plugin = ClickHouseServicePlugin()
> > > plugin.metadata.name
> > > 'clickhouse'

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ClickHouseServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseServicePlugin&#x22;" />

      <Card title="&#x22;ClickHouseSetupServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseSetupServicePlugin&#x22;" />

      <Card title="&#x22;ClickHouseResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseResourceProvider&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_service_definition&#x22;" type="&#x22;(resource_name, service_name) -> dict[str, Any]&#x22;">
      Load and parse a YAML service definition from package resources.

      Reads a YAML service configuration file bundled with the package and
      parses it into a Python dictionary. Logs performance metrics and errors.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > definition = \_load\_service\_definition("service.yaml", "clickhouse")
        > > > "services" in definition
        > > > True
      </Callout>

      <PySourceCode>
        ```python
        def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
            """Load and parse a YAML service definition from package resources.

            Reads a YAML service configuration file bundled with the package and
            parses it into a Python dictionary. Logs performance metrics and errors.

            Args:
                resource_name: Name of the YAML resource file to load.
                service_name: Identifier for the service being loaded (used in logs).

            Returns:
                Parsed YAML content as a dictionary.

            Raises:
                Exception: If the YAML file cannot be read or parsed. The error is
                    logged with context before being re-raised.

            Example:
                >>> definition = _load_service_definition("service.yaml", "clickhouse")
                >>> "services" in definition
                True

            """
            start = perf_counter()
            logger.info(
                "clickhouse_service_definition_load_started",
                service_name=service_name,
                resource_name=resource_name,
            )
            service_path = resources.files("phlo_clickhouse").joinpath(resource_name)
            try:
                data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
            except Exception:
                logger.error(
                    "clickhouse_service_definition_load_failed",
                    service_name=service_name,
                    resource_name=resource_name,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise

            service_count = len(data.get("services", {})) if isinstance(data, dict) else None
            logger.info(
                "clickhouse_service_definition_load_completed",
                service_name=service_name,
                resource_name=resource_name,
                elapsed_ms=round((perf_counter() - start) * 1000, 2),
                service_count=service_count,
            )
            return data
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;resource_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the YAML resource file to load.
        </PyParameter>

        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Identifier for the service being loaded (used in logs).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Parsed YAML content as a dictionary.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
