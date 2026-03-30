# plugin (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin)



RustFS service plugin.

This module implements Phlo plugins for integrating RustFS into the service mesh.
It provides service definitions for running RustFS containers and initializing
buckets, plus resource providers that expose S3-compatible object storage
capabilities to other components.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RustfsServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsServicePlugin&#x22;" />

      <Card title="&#x22;RustfsSetupServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsSetupServicePlugin&#x22;" />

      <Card title="&#x22;RustfsObjectStoreProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsObjectStoreProvider&#x22;" />

      <Card title="&#x22;RustfsResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsResourceProvider&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_service_definition&#x22;" type="&#x22;(resource_name, service_name) -> dict[str, Any]&#x22;">
      Load a YAML service definition from package resources.

      Reads a YAML file containing Docker Compose-style service definitions
      from the phlo\_rustfs package resources. Includes structured logging
      for performance monitoring and error tracking.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > definition = \_load\_service\_definition("service.yaml", "rustfs")
        > > > print(definition\["name"])
        > > > "rustfs"
      </Callout>

      <PySourceCode>
        ```python
        def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
            """Load a YAML service definition from package resources.

            Reads a YAML file containing Docker Compose-style service definitions
            from the phlo_rustfs package resources. Includes structured logging
            for performance monitoring and error tracking.

            Args:
                resource_name: Name of the YAML resource file to load.
                service_name: Logical name of the service for logging purposes.

            Returns:
                Dictionary containing the parsed YAML service definition.

            Raises:
                Exception: If the YAML file cannot be read or parsed.

            Example:
                >>> definition = _load_service_definition("service.yaml", "rustfs")
                >>> print(definition["name"])
                "rustfs"

            """
            start = perf_counter()
            logger.info(
                "rustfs_service_definition_load_started",
                service_name=service_name,
                resource_name=resource_name,
            )
            service_path = resources.files("phlo_rustfs").joinpath(resource_name)
            try:
                data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
            except Exception:
                logger.error(
                    "rustfs_service_definition_load_failed",
                    service_name=service_name,
                    resource_name=resource_name,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise

            service_count = len(data.get("services", {})) if isinstance(data, dict) else None
            logger.info(
                "rustfs_service_definition_load_completed",
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
          Logical name of the service for logging purposes.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary containing the parsed YAML service definition.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
