# plugin (/docs/python-reference/packages/phlo-minio/phlo_minio/plugin)



MinIO service and resource provider plugin for Phlo.

This module provides the complete MinIO integration for Phlo, including:

* Service plugin for MinIO server deployment
* Bucket initialization (setup) service
* Object storage capability provider
* Resource provider for S3-compatible storage

The module implements Phlo's plugin interfaces to provide S3-compatible
object storage capabilities for data lake operations.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MinioServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioServicePlugin&#x22;" />

      <Card title="&#x22;MinioSetupServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioSetupServicePlugin&#x22;" />

      <Card title="&#x22;MinioObjectStoreProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioObjectStoreProvider&#x22;" />

      <Card title="&#x22;MinioResourceProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioResourceProvider&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_service_definition&#x22;" type="&#x22;(resource_name, service_name) -> dict[str, Any]&#x22;">
      Load and parse a YAML service definition file.

      Reads a YAML service definition from the package resources and
      returns the parsed configuration. Includes performance logging
      for monitoring load times.

      <Callout title="&#x22;Logging&#x22;" type="&#x22;logging&#x22;">
        Emits structured logs:

        * minio\_service\_definition\_load\_started: When loading begins
        * minio\_service\_definition\_load\_completed: On success with timing
        * minio\_service\_definition\_load\_failed: On failure with timing
      </Callout>

      <Callout title="&#x22;Implementation&#x22;" type="&#x22;implementation&#x22;">
        Uses importlib.resources for package-relative file access:
        service\_path = resources.files("phlo\_minio").joinpath(resource\_name)
      </Callout>

      <PySourceCode>
        ```python
        def _load_service_definition(resource_name: str, service_name: str) -> dict[str, Any]:
            """Load and parse a YAML service definition file.

            Reads a YAML service definition from the package resources and
            returns the parsed configuration. Includes performance logging
            for monitoring load times.

            Args:
                resource_name: Name of the YAML file in the package (e.g., "service.yaml").
                service_name: Logical name of the service for logging purposes.

            Returns:
                dict[str, Any]: Parsed YAML service definition.

            Raises:
                Exception: If file reading or YAML parsing fails. Error is logged
                    with timing information before re-raising.

            Examples:
                Load MinIO service definition:
                    >>> defn = _load_service_definition("service.yaml", "minio")
                    >>> print(defn['services']['minio']['image'])
                    'minio/minio:latest'

                Load setup service:
                    >>> defn = _load_service_definition("minio-setup.yaml", "minio-setup")
                    >>> print(defn['services']['minio-setup']['command'])
                    ['sh', '-c', '...']

            Logging:
                Emits structured logs:
                    - minio_service_definition_load_started: When loading begins
                    - minio_service_definition_load_completed: On success with timing
                    - minio_service_definition_load_failed: On failure with timing

            Implementation:
                Uses importlib.resources for package-relative file access:
                    service_path = resources.files("phlo_minio").joinpath(resource_name)

            """
            start = perf_counter()
            logger.info(
                "minio_service_definition_load_started",
                service_name=service_name,
                resource_name=resource_name,
            )
            service_path = resources.files("phlo_minio").joinpath(resource_name)
            try:
                data = yaml.safe_load(service_path.read_text(encoding="utf-8"))
            except Exception:
                logger.error(
                    "minio_service_definition_load_failed",
                    service_name=service_name,
                    resource_name=resource_name,
                    elapsed_ms=round((perf_counter() - start) * 1000, 2),
                    exc_info=True,
                )
                raise

            service_count = len(data.get("services", {})) if isinstance(data, dict) else None
            logger.info(
                "minio_service_definition_load_completed",
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
          Name of the YAML file in the package (e.g., "service.yaml").
        </PyParameter>

        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Logical name of the service for logging purposes.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, Any]: Parsed YAML service definition.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
